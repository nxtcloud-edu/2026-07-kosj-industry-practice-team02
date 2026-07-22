from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import date
from uuid import UUID

import pytest

from sejong_ai_api.chat.context import ContextTokenCodec
from sejong_ai_api.chat.service import ChatService, ChatUnavailableError
from sejong_ai_api.contracts.chat import ChatRequest
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

REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")
INTERACTION_ID = UUID("22222222-2222-4222-8222-222222222222")


def knowledge_record(
    *,
    intent: Intent = Intent.BULKY_WASTE,
    service_name: str = "대형폐기물 배출신청 절차",
    question_examples: tuple[str, ...] = ("대형폐기물은 어떻게 버려요?",),
    required_documents: tuple[str, ...] = (),
) -> KnowledgeRecord:
    return KnowledgeRecord(
        public_id="KB-TEST-01",
        category=intent,
        service_name=service_name,
        answer_summary="승인된 안내 요약입니다.",
        procedure_steps=("승인된 절차를 확인하세요.",),
        required_documents=required_documents,
        processing_time=None,
        fee=None,
        department="민원 담당 부서",
        source_title="승인된 공식 출처",
        source_url="https://example.invalid/official/source",
        last_verified_at=date(2026, 7, 20),
        caution=None,
        question_examples=question_examples,
    )


def office_record(
    *,
    region: Region = Region.AREUM_DONG,
    intent: Intent = Intent.BULKY_WASTE,
) -> OfficeRecord:
    del intent
    return OfficeRecord(
        public_id="OFFICE-TEST-01",
        region=region,
        office_name="아름동 행정복지센터",
        address="세종특별자치시 시연용 주소",
        phone="044-000-0000",
        opening_hours="평일 09:00~18:00",
        map_url=None,
        department_label="민원창구",
        source_title="승인된 기관 출처",
        source_url="https://example.invalid/official/office",
        last_verified_at=date(2026, 7, 20),
    )


class FakeRepository:
    def __init__(
        self,
        *,
        records: Sequence[KnowledgeRecord] = (),
        offices: Sequence[OfficeRecord] = (),
        fail_reads: bool = False,
        fail_event_write: bool = False,
    ) -> None:
        self.records = tuple(records)
        self.offices = tuple(offices)
        self.fail_reads = fail_reads
        self.fail_event_write = fail_event_write
        self.active_intents: list[Intent] = []
        self.office_queries: list[tuple[Region, Intent]] = []
        self.events: list[InteractionWrite] = []

    async def list_active_kb(self, intent: Intent) -> Sequence[KnowledgeRecord]:
        self.active_intents.append(intent)
        if self.fail_reads:
            raise DatabaseUnavailableError()
        return self.records

    async def list_offices(self, region: Region, intent: Intent) -> Sequence[OfficeRecord]:
        self.office_queries.append((region, intent))
        if self.fail_reads:
            raise DatabaseUnavailableError()
        return self.offices

    async def record_interaction(self, event: InteractionWrite) -> InteractionWriteResult:
        self.events.append(event)
        if self.fail_event_write:
            raise DatabaseUnavailableError()
        return InteractionWriteResult(INTERACTION_ID, None)


def service(
    repository: FakeRepository,
    *,
    clock_ns: Callable[[], int] | None = None,
) -> ChatService:
    ticks = iter((1_000_000, 6_000_000))
    return ChatService(
        repository=repository,
        context_codec=ContextTokenCodec(secret=b"x" * 32, clock=lambda: 1_000),
        request_id_factory=lambda: REQUEST_ID,
        monotonic_ns=clock_ns if clock_ns is not None else lambda: next(ticks),
        is_test=True,
    )


@pytest.mark.asyncio
async def test_success_uses_masked_text_for_lookup_and_server_bound_metadata() -> None:
    raw_phone = "010-1234-5678"
    record = knowledge_record(
        question_examples=("대형폐기물은 어떻게 버려요?",),
    )
    repository = FakeRepository(records=(record,), offices=(office_record(),))

    response = await service(repository).answer(
        ChatRequest(
            question=f"대형폐기물은 어떻게 버려요? 연락처는 {raw_phone}",
            selected_region="아름동",
        )
    )

    assert response.answer_status == "SUCCESS"
    assert response.intent == Intent.BULKY_WASTE.value
    assert response.sources[0].source_id == record.public_id
    assert response.office is not None
    assert response.office.id == "OFFICE-TEST-01"
    assert response.context_token is not None
    assert raw_phone not in response.context_token
    assert repository.active_intents == [Intent.BULKY_WASTE]
    assert repository.office_queries == [(Region.AREUM_DONG, Intent.BULKY_WASTE)]
    assert len(repository.events) == 1
    event = repository.events[0]
    assert event.answer_status is AnswerStatus.SUCCESS
    assert event.used_source_ids == (record.public_id,)
    assert event.masked_question is None
    assert event.response_time_ms == 5
    assert raw_phone not in repr(repository.events)


@pytest.mark.asyncio
async def test_privacy_unresolved_returns_fixed_fallback_and_uses_no_repository() -> None:
    repository = FakeRepository(fail_reads=True)

    response = await service(repository).answer(ChatRequest(question="김철수"))

    assert response.answer_status == "FALLBACK"
    assert response.intent == Intent.UNKNOWN.value
    assert response.fallback.reason == "PRIVACY_UNRESOLVED"
    assert response.fallback.candidate_eligible is False
    assert response.sources == []
    assert response.context_token is None
    assert repository.active_intents == []
    assert repository.office_queries == []
    assert repository.events == []


@pytest.mark.asyncio
async def test_ambiguous_question_is_followup_and_never_creates_a_failed_question() -> None:
    repository = FakeRepository()

    response = await service(repository).answer(ChatRequest(question="신고하고 싶어요."))

    assert response.answer_status == "FOLLOWUP"
    assert response.intent == Intent.UNKNOWN.value
    assert len(response.followup_options) == 4
    assert response.context_token is not None
    assert repository.active_intents == []
    assert len(repository.events) == 1
    assert repository.events[0].answer_status is AnswerStatus.FOLLOWUP
    assert repository.events[0].masked_question is None


@pytest.mark.asyncio
async def test_signed_context_resolves_a_short_followup_without_storing_transcript() -> None:
    record = knowledge_record(
        intent=Intent.MOVE_IN_RESIDENT_REGISTRATION,
        service_name="방문 전입신고 준비물",
        question_examples=("전입신고 준비물은 무엇인가요?",),
        required_documents=("신분증",),
    )
    repository = FakeRepository(records=(record,))
    codec = ContextTokenCodec(secret=b"x" * 32, clock=lambda: 1_000)
    token = codec.issue(
        last_intent=Intent.MOVE_IN_RESIDENT_REGISTRATION.value,
        selected_region=None,
        answer_status="SUCCESS",
    )
    ticks = iter((1_000_000, 2_000_000))
    chat_service = ChatService(
        repository=repository,
        context_codec=codec,
        request_id_factory=lambda: REQUEST_ID,
        monotonic_ns=lambda: next(ticks),
        is_test=True,
    )

    response = await chat_service.answer(ChatRequest(question="준비물은요?", context_token=token))

    assert response.answer_status == "SUCCESS"
    assert response.intent == Intent.MOVE_IN_RESIDENT_REGISTRATION.value
    assert repository.active_intents == [Intent.MOVE_IN_RESIDENT_REGISTRATION]


@pytest.mark.asyncio
async def test_invalid_context_silently_resets_to_followup() -> None:
    repository = FakeRepository()

    response = await service(repository).answer(
        ChatRequest(question="준비물은요?", context_token="tampered.token")
    )

    assert response.answer_status == "FOLLOWUP"
    assert response.intent == Intent.UNKNOWN.value
    assert repository.active_intents == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("question", "reason", "intent", "masked_is_stored"),
    [
        (
            "침대 프레임 배출 수수료를 알려줘.",
            FallbackReason.INSUFFICIENT_GROUNDING,
            Intent.BULKY_WASTE,
            True,
        ),
        (
            "내 자동차세 체납액을 조회해줘.",
            FallbackReason.PERSONAL_LOOKUP,
            Intent.LOCAL_TAX_GENERAL,
            True,
        ),
        (
            "전입신고를 안 하면 법적으로 처벌받는지 판단해줘.",
            FallbackReason.LEGAL_JUDGMENT,
            Intent.MOVE_IN_RESIDENT_REGISTRATION,
            True,
        ),
        (
            "오늘 세종시 날씨를 알려줘.",
            FallbackReason.OUT_OF_SCOPE,
            Intent.OUT_OF_SCOPE,
            False,
        ),
    ],
)
async def test_policy_fallback_event_matrix(
    question: str,
    reason: FallbackReason,
    intent: Intent,
    masked_is_stored: bool,
) -> None:
    repository = FakeRepository()

    response = await service(repository).answer(ChatRequest(question=question))

    assert response.answer_status == "FALLBACK"
    assert response.fallback.reason == reason.value
    assert response.context_token is None
    assert len(repository.events) == 1
    event = repository.events[0]
    assert event.intent is intent
    assert event.fallback_reason is reason
    assert (event.masked_question is not None) is masked_is_stored


@pytest.mark.asyncio
async def test_required_kb_read_failure_is_a_value_free_unavailable_error() -> None:
    repository = FakeRepository(fail_reads=True)

    with pytest.raises(ChatUnavailableError, match="^CHAT_UNAVAILABLE$") as captured:
        await service(repository).answer(ChatRequest(question="대형폐기물 배출 방법"))

    assert "대형폐기물" not in repr(captured.value)
    assert repository.events == []


@pytest.mark.asyncio
async def test_event_write_failure_does_not_discard_an_already_safe_answer() -> None:
    repository = FakeRepository(
        records=(knowledge_record(),),
        fail_event_write=True,
    )

    response = await service(repository).answer(ChatRequest(question="대형폐기물은 어떻게 버려요?"))

    assert response.answer_status == "SUCCESS"
    assert len(repository.events) == 1
