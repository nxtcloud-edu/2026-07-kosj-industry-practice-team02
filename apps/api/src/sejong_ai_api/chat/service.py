"""Privacy-first deterministic chat orchestration."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Sequence
from typing import Literal, Protocol, cast
from uuid import UUID

from sejong_ai_api.chat.classification import SafeQuestion, classify_question
from sejong_ai_api.chat.context import ChatContext, ContextTokenCodec
from sejong_ai_api.chat.grounding import evaluate_grounding
from sejong_ai_api.chat.response import (
    build_fallback_response,
    build_followup_response,
    build_success_response,
)
from sejong_ai_api.chat.retrieval import RankedKnowledge, rank_active_knowledge
from sejong_ai_api.contracts.chat import (
    ChatRequest,
    FallbackResponse,
    FollowupResponse,
    SuccessResponse,
)
from sejong_ai_api.db.errors import DatabaseUnavailableError
from sejong_ai_api.db.models import (
    AnswerStatus,
    FallbackReason,
    Intent,
    InteractionWrite,
    InteractionWriteResult,
    KnowledgeRecord,
    OfficeRecord,
    Region,
)
from sejong_ai_api.privacy.redaction import redact_question

type ChatResult = SuccessResponse | FollowupResponse | FallbackResponse
type SupportedIntentValue = Literal[
    "MOVE_IN_RESIDENT_REGISTRATION",
    "CERTIFICATE_ISSUANCE",
    "BULKY_WASTE",
    "LOCAL_TAX_GENERAL",
]
_SUPPORTED_INTENTS = frozenset(
    {
        Intent.MOVE_IN_RESIDENT_REGISTRATION,
        Intent.CERTIFICATE_ISSUANCE,
        Intent.BULKY_WASTE,
        Intent.LOCAL_TAX_GENERAL,
    }
)
_FOLLOWUP_OPTIONS: tuple[
    Literal[
        "intent.move-in",
        "intent.certificate",
        "intent.bulky-waste",
        "intent.local-tax",
    ],
    ...,
] = (
    "intent.move-in",
    "intent.certificate",
    "intent.bulky-waste",
    "intent.local-tax",
)
_CONTEXT_DETAIL_TERMS = (
    "준비물",
    "서류",
    "수수료",
    "비용",
    "기간",
    "처리시간",
    "어디",
    "방문",
    "온라인",
    "신청",
    "발급",
    "배출",
    "납부",
)
_EXPLICIT_INTENT_TERMS = (
    "전입",
    "주민등록",
    "등본",
    "초본",
    "증명서",
    "대형폐기물",
    "폐기물",
    "지방세",
    "자동차세",
    "재산세",
    "주민세",
    "취득세",
)


class ChatRepository(Protocol):
    async def list_active_kb(self, intent: Intent) -> Sequence[KnowledgeRecord]: ...

    async def list_offices(self, region: Region, intent: Intent) -> Sequence[OfficeRecord]: ...

    async def record_interaction(self, event: InteractionWrite) -> InteractionWriteResult: ...


class ChatUnavailableError(Exception):
    """A value-free signal that no safe grounded response can be produced."""

    def __init__(self) -> None:
        super().__init__("CHAT_UNAVAILABLE")


class ChatService:
    """Compose redaction, policy, retrieval, grounding, response and event gates."""

    def __init__(
        self,
        *,
        repository: ChatRepository,
        context_codec: ContextTokenCodec,
        request_id_factory: Callable[[], UUID],
        monotonic_ns: Callable[[], int],
        is_test: bool,
    ) -> None:
        if not callable(request_id_factory) or not callable(monotonic_ns):
            raise TypeError("CHAT_SERVICE_DEPENDENCY_INVALID")
        if type(is_test) is not bool:
            raise TypeError("CHAT_SERVICE_DEPENDENCY_INVALID")
        self._repository = repository
        self._context_codec = context_codec
        self._request_id_factory = request_id_factory
        self._monotonic_ns = monotonic_ns
        self._is_test = is_test

    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
    ) -> ChatResult:
        """Return one safe contract response or a value-free unavailable signal."""

        if type(request) is not ChatRequest:
            raise TypeError("CHAT_REQUEST_REQUIRED")
        selected_request_id = request_id if request_id is not None else self._request_id_factory()
        if type(selected_request_id) is not UUID:
            raise TypeError("REQUEST_ID_FACTORY_INVALID")
        started_ns = self._read_monotonic_ns()

        redaction = redact_question(request.question)
        if redaction.masked_text is None:
            return build_fallback_response(
                request_id=selected_request_id,
                intent=Intent.UNKNOWN,
                reason="PRIVACY_UNRESOLVED",
                office=None,
            )

        safe_question = SafeQuestion(redaction)
        prior_context = self._context_codec.read(request.context_token)
        selected_region = _selected_region(request.selected_region, prior_context)
        outcome = classify_question(safe_question)
        intent = outcome.intent
        intent_from_context = False
        if (
            outcome.followup_required
            and prior_context is not None
            and _is_contextual_followup(safe_question.text)
        ):
            prior_intent = Intent(prior_context.last_intent)
            if prior_intent in _SUPPORTED_INTENTS:
                intent = prior_intent
                intent_from_context = True

        if outcome.fallback_reason is FallbackReason.OUT_OF_SCOPE:
            fallback_response = build_fallback_response(
                request_id=selected_request_id,
                intent=Intent.OUT_OF_SCOPE,
                reason="OUT_OF_SCOPE",
                office=None,
            )
            await self._record_best_effort(
                request_id=selected_request_id,
                intent=Intent.OUT_OF_SCOPE,
                answer_status=AnswerStatus.FALLBACK,
                fallback_reason=FallbackReason.OUT_OF_SCOPE,
                used_source_ids=(),
                selected_region=selected_region,
                office=None,
                masked_question=None,
                started_ns=started_ns,
            )
            return fallback_response

        if outcome.fallback_reason in {
            FallbackReason.PERSONAL_LOOKUP,
            FallbackReason.LEGAL_JUDGMENT,
        }:
            office = await self._load_optional_office(selected_region, intent)
            reason = cast(FallbackReason, outcome.fallback_reason)
            fallback_response = build_fallback_response(
                request_id=selected_request_id,
                intent=intent,
                reason=cast(
                    Literal["PERSONAL_LOOKUP", "LEGAL_JUDGMENT"],
                    reason.value,
                ),
                office=office,
            )
            await self._record_best_effort(
                request_id=selected_request_id,
                intent=intent,
                answer_status=AnswerStatus.FALLBACK,
                fallback_reason=reason,
                used_source_ids=(),
                selected_region=selected_region,
                office=office,
                masked_question=safe_question.text,
                started_ns=started_ns,
            )
            return fallback_response

        if intent is Intent.UNKNOWN:
            token = self._issue_context(
                intent=Intent.UNKNOWN,
                selected_region=selected_region,
                answer_status="FOLLOWUP",
            )
            followup_response = build_followup_response(
                request_id=selected_request_id,
                intent=Intent.UNKNOWN,
                confidence=None,
                option_ids=_FOLLOWUP_OPTIONS,
                context_token=token,
            )
            await self._record_best_effort(
                request_id=selected_request_id,
                intent=Intent.UNKNOWN,
                answer_status=AnswerStatus.FOLLOWUP,
                fallback_reason=None,
                used_source_ids=(),
                selected_region=selected_region,
                office=None,
                masked_question=None,
                started_ns=started_ns,
            )
            return followup_response

        ranked = await self._ranked_knowledge(safe_question, intent)
        top = ranked[0] if ranked else None
        grounding = evaluate_grounding(
            safe_question,
            intent,
            top.record if top is not None else None,
            allow_contextual_detail=intent_from_context,
        )
        if not grounding.is_grounded or grounding.record is None:
            office = await self._load_optional_office(selected_region, intent)
            fallback_response = build_fallback_response(
                request_id=selected_request_id,
                intent=intent,
                reason="INSUFFICIENT_GROUNDING",
                office=office,
            )
            await self._record_best_effort(
                request_id=selected_request_id,
                intent=intent,
                answer_status=AnswerStatus.FALLBACK,
                fallback_reason=FallbackReason.INSUFFICIENT_GROUNDING,
                used_source_ids=(),
                selected_region=selected_region,
                office=office,
                masked_question=safe_question.text,
                started_ns=started_ns,
            )
            return fallback_response

        office = await self._load_optional_office(selected_region, intent)
        token = self._issue_context(
            intent=intent,
            selected_region=selected_region,
            answer_status="SUCCESS",
        )
        success_response = build_success_response(
            request_id=selected_request_id,
            record=grounding.record,
            office=office,
            confidence=_confidence(top),
            context_token=token,
        )
        await self._record_best_effort(
            request_id=selected_request_id,
            intent=intent,
            answer_status=AnswerStatus.SUCCESS,
            fallback_reason=None,
            used_source_ids=(grounding.record.public_id,),
            selected_region=selected_region,
            office=office,
            masked_question=None,
            started_ns=started_ns,
        )
        return success_response

    async def _ranked_knowledge(
        self,
        question: SafeQuestion,
        intent: Intent,
    ) -> tuple[RankedKnowledge, ...]:
        try:
            records = await self._repository.list_active_kb(intent)
        except DatabaseUnavailableError:
            raise ChatUnavailableError() from None
        return rank_active_knowledge(question, intent, records)

    async def _load_optional_office(
        self,
        selected_region: Region | None,
        intent: Intent,
    ) -> OfficeRecord | None:
        if selected_region is None or intent not in _SUPPORTED_INTENTS:
            return None
        try:
            offices = await self._repository.list_offices(selected_region, intent)
        except DatabaseUnavailableError:
            return None
        return offices[0] if offices else None

    def _issue_context(
        self,
        *,
        intent: Intent,
        selected_region: Region | None,
        answer_status: Literal["SUCCESS", "FOLLOWUP"],
    ) -> str:
        return self._context_codec.issue(
            last_intent=intent.value,
            selected_region=selected_region.value if selected_region is not None else None,
            answer_status=answer_status,
        )

    async def _record_best_effort(
        self,
        *,
        request_id: UUID,
        intent: Intent,
        answer_status: AnswerStatus,
        fallback_reason: FallbackReason | None,
        used_source_ids: tuple[str, ...],
        selected_region: Region | None,
        office: OfficeRecord | None,
        masked_question: str | None,
        started_ns: int,
    ) -> None:
        event = InteractionWrite(
            request_id=request_id,
            intent=intent,
            answer_status=answer_status,
            fallback_reason=fallback_reason,
            used_source_ids=used_source_ids,
            response_time_ms=max(0, (self._read_monotonic_ns() - started_ns) // 1_000_000),
            selected_region=selected_region,
            routed_office_public_id=office.public_id if office is not None else None,
            is_test=self._is_test,
            masked_question=masked_question,
        )
        try:
            await self._repository.record_interaction(event)
        except DatabaseUnavailableError:
            return

    def _read_monotonic_ns(self) -> int:
        value = self._monotonic_ns()
        if type(value) is not int or value < 0:
            raise TypeError("MONOTONIC_CLOCK_INVALID")
        return value


def _selected_region(selected: str | None, context: ChatContext | None) -> Region | None:
    if selected is not None:
        return Region(selected)
    if context is None:
        return None
    return Region(context.selected_region) if context.selected_region is not None else None


def _is_contextual_followup(value: str) -> bool:
    compact = re.sub(
        r"[^0-9a-z가-힣]",
        "",
        unicodedata.normalize("NFKC", value).casefold(),
    )
    return any(term in compact for term in _CONTEXT_DETAIL_TERMS) and not any(
        term in compact for term in _EXPLICIT_INTENT_TERMS
    )


def _confidence(item: RankedKnowledge | None) -> float:
    if item is None:
        raise ValueError("RANKED_KNOWLEDGE_REQUIRED")
    if item.exact_question_match:
        return 0.99
    overlap = item.service_or_example_overlap + item.procedure_document_overlap
    return min(0.95, 0.7 + overlap * 0.05)


__all__ = ["ChatRepository", "ChatResult", "ChatService", "ChatUnavailableError"]
