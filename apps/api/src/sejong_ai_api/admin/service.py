"""Fail-closed local/private administrator workflow orchestration."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Literal, Protocol, TypeVar
from uuid import UUID

from sejong_ai_api.contracts.admin import (
    CandidateReviewRequest,
    FailedQuestion,
    FailedQuestionDetailResponse,
    FailedQuestionListResponse,
    KBCandidateCreateRequest,
    KBCandidateCreateResponse,
    KBCandidateListResponse,
    KBCandidateReviewResponse,
    KBCandidateSubmitResponse,
    KBCandidateSummary,
    ReasonConfirmationRequest,
    ReasonConfirmationResponse,
)
from sejong_ai_api.db.errors import (
    DatabaseRuleCode,
    DatabaseRuleError,
    DatabaseUnavailableError,
)
from sejong_ai_api.db.models import (
    Actor,
    AdminRole,
    CandidateDraft,
    DataOrigin,
    FallbackReason,
    Intent,
    PurgeResult,
)
from sejong_ai_api.privacy import redact_question

type AdminErrorCode = Literal[
    "ADMIN_ROUTE_DISABLED",
    "ADMIN_FORBIDDEN",
    "ADMIN_NOT_FOUND",
    "ADMIN_INVALID_STATE",
    "ADMIN_VALIDATION_FAILED",
]

_FAILURE_REASONS = frozenset({"INSUFFICIENT_GROUNDING", "PERSONAL_LOOKUP", "LEGAL_JUDGMENT"})
_FAILURE_STATUSES = frozenset({"NEW", "REASON_CONFIRMED"})


class AdminServiceError(Exception):
    """Stable value-free application error translated by the HTTP adapter."""

    def __init__(self, code: AdminErrorCode) -> None:
        self.code = code
        super().__init__("ADMIN_OPERATION_REJECTED")


class AdminRepository(Protocol):
    """Admin read port plus the existing constrained DB write capabilities."""

    async def list_failed_questions(
        self, *, reason: str | None, status: str | None
    ) -> Sequence[FailedQuestion]: ...

    async def get_failed_question(self, failed_question_id: UUID) -> FailedQuestion | None: ...

    async def list_kb_candidates(self) -> Sequence[KBCandidateSummary]: ...

    async def get_kb_candidate(self, candidate_id: UUID) -> KBCandidateSummary | None: ...

    async def purge_expired_failed_question_text(self) -> PurgeResult: ...

    async def confirm_failed_question_reason(
        self,
        failed_question_id: UUID,
        actor: Actor,
        fallback_reason: FallbackReason,
    ) -> None: ...

    async def create_kb_candidate(self, draft: CandidateDraft) -> UUID: ...

    async def submit_kb_candidate(self, candidate_id: UUID, actor: Actor) -> None: ...

    async def approve_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> str: ...

    async def reject_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> None: ...


T = TypeVar("T")


class AdminService:
    """Enforce role and workflow rules before the DB enforces them again."""

    def __init__(self, repository: AdminRepository) -> None:
        self._repository = repository

    async def list_failed_questions(
        self,
        actor: Actor,
        *,
        reason: str | None,
        status: str | None,
    ) -> FailedQuestionListResponse:
        self._require_admin(actor)
        if reason is not None and reason not in _FAILURE_REASONS:
            raise AdminServiceError("ADMIN_VALIDATION_FAILED")
        if status is not None and status not in _FAILURE_STATUSES:
            raise AdminServiceError("ADMIN_VALIDATION_FAILED")
        await self._safe_call(self._repository.purge_expired_failed_question_text)
        items = await self._safe_call(
            lambda: self._repository.list_failed_questions(reason=reason, status=status)
        )
        return FailedQuestionListResponse(items=list(items), total=len(items))

    async def get_failed_question(
        self,
        actor: Actor,
        failed_question_id: UUID,
    ) -> FailedQuestionDetailResponse:
        self._require_admin(actor)
        await self._safe_call(self._repository.purge_expired_failed_question_text)
        item = await self._safe_call(
            lambda: self._repository.get_failed_question(failed_question_id)
        )
        if item is None:
            raise AdminServiceError("ADMIN_NOT_FOUND")
        return FailedQuestionDetailResponse(item=item)

    async def confirm_reason(
        self,
        actor: Actor,
        failed_question_id: UUID,
        payload: ReasonConfirmationRequest,
    ) -> ReasonConfirmationResponse:
        self._require_role(actor, AdminRole.OPERATOR)
        current = await self._get_failure_for_change(failed_question_id)
        if current.status != "NEW":
            raise AdminServiceError("ADMIN_INVALID_STATE")
        fallback_reason = FallbackReason(payload.reason)
        await self._safe_call(
            lambda: self._repository.confirm_failed_question_reason(
                failed_question_id,
                actor,
                fallback_reason,
            )
        )
        return ReasonConfirmationResponse(id=failed_question_id, status="REASON_CONFIRMED")

    async def list_candidates(self, actor: Actor) -> KBCandidateListResponse:
        self._require_admin(actor)
        items = await self._safe_call(self._repository.list_kb_candidates)
        return KBCandidateListResponse(items=list(items), total=len(items))

    async def create_candidate(
        self,
        actor: Actor,
        payload: KBCandidateCreateRequest,
    ) -> KBCandidateCreateResponse:
        self._require_role(actor, AdminRole.OPERATOR)
        failure = await self._get_failure_for_change(payload.failed_question_id)
        if (
            failure.status != "REASON_CONFIRMED"
            or failure.fallback_reason != "INSUFFICIENT_GROUNDING"
            or not failure.candidate_eligible
        ):
            raise AdminServiceError("ADMIN_INVALID_STATE")
        self._require_privacy_safe_candidate(payload)
        try:
            draft = CandidateDraft(
                failed_question_id=payload.failed_question_id,
                actor=actor,
                title=payload.title,
                representative_question=payload.representative_question,
                category=Intent(payload.category),
                answer_summary=payload.answer_summary,
                procedure_steps=tuple(payload.procedure_steps),
                required_documents=tuple(payload.required_documents),
                processing_time=payload.processing_time,
                fee=payload.fee,
                department=payload.department,
                source_title=payload.source_title,
                source_url=str(payload.source_url),
                last_verified_at=payload.last_verified_at,
                caution=payload.caution,
                data_origin=DataOrigin.OFFICIAL,
            )
        except ValueError:
            raise AdminServiceError("ADMIN_VALIDATION_FAILED") from None
        candidate_id = await self._safe_call(lambda: self._repository.create_kb_candidate(draft))
        return KBCandidateCreateResponse(id=candidate_id, status="DRAFTED")

    async def submit_candidate(
        self,
        actor: Actor,
        candidate_id: UUID,
    ) -> KBCandidateSubmitResponse:
        self._require_role(actor, AdminRole.OPERATOR)
        candidate = await self._get_candidate_for_change(candidate_id)
        if candidate.status != "DRAFTED":
            raise AdminServiceError("ADMIN_INVALID_STATE")
        if candidate.created_by != actor.actor_id:
            raise AdminServiceError("ADMIN_FORBIDDEN")
        await self._safe_call(lambda: self._repository.submit_kb_candidate(candidate_id, actor))
        return KBCandidateSubmitResponse(id=candidate_id, status="PENDING_APPROVAL")

    async def review_candidate(
        self,
        actor: Actor,
        candidate_id: UUID,
        payload: CandidateReviewRequest,
    ) -> KBCandidateReviewResponse:
        self._require_role(actor, AdminRole.APPROVER)
        candidate = await self._get_candidate_for_change(candidate_id)
        if candidate.status != "PENDING_APPROVAL":
            raise AdminServiceError("ADMIN_INVALID_STATE")
        if candidate.created_by == actor.actor_id:
            raise AdminServiceError("ADMIN_FORBIDDEN")
        if payload.decision == "APPROVED":
            await self._safe_call(
                lambda: self._repository.approve_kb_candidate(
                    candidate_id,
                    actor,
                    payload.review_comment,
                )
            )
        else:
            await self._safe_call(
                lambda: self._repository.reject_kb_candidate(
                    candidate_id,
                    actor,
                    payload.review_comment,
                )
            )
        return KBCandidateReviewResponse(id=candidate_id, status=payload.decision)

    async def _get_failure_for_change(self, failed_question_id: UUID) -> FailedQuestion:
        item = await self._safe_call(
            lambda: self._repository.get_failed_question(failed_question_id)
        )
        if item is None:
            raise AdminServiceError("ADMIN_NOT_FOUND")
        return item

    async def _get_candidate_for_change(self, candidate_id: UUID) -> KBCandidateSummary:
        item = await self._safe_call(lambda: self._repository.get_kb_candidate(candidate_id))
        if item is None:
            raise AdminServiceError("ADMIN_NOT_FOUND")
        return item

    @staticmethod
    def _require_admin(actor: Actor) -> None:
        if type(actor) is not Actor or actor.role not in {
            AdminRole.OPERATOR,
            AdminRole.APPROVER,
        }:
            raise AdminServiceError("ADMIN_FORBIDDEN")

    @staticmethod
    def _require_role(actor: Actor, role: AdminRole) -> None:
        if type(actor) is not Actor or actor.role is not role:
            raise AdminServiceError("ADMIN_FORBIDDEN")

    @staticmethod
    def _require_privacy_safe_candidate(payload: KBCandidateCreateRequest) -> None:
        values = (
            payload.title,
            payload.representative_question,
            payload.answer_summary,
            *payload.procedure_steps,
            *payload.required_documents,
            payload.processing_time,
            payload.fee,
            payload.department,
            payload.source_title,
            payload.caution,
        )
        for value in values:
            if value is None:
                continue
            result = redact_question(value)
            if result.masked_text is None or result.masked_text != value or result.findings:
                raise AdminServiceError("ADMIN_VALIDATION_FAILED")

    @staticmethod
    async def _safe_call(operation: Callable[[], Awaitable[T]]) -> T:
        try:
            return await operation()
        except DatabaseRuleError as exc:
            if exc.code in {
                DatabaseRuleCode.FORBIDDEN_ACTOR_ROLE,
                DatabaseRuleCode.SELF_APPROVAL,
            }:
                raise AdminServiceError("ADMIN_FORBIDDEN") from None
            if exc.code in {
                DatabaseRuleCode.INCOMPLETE_CANDIDATE,
                DatabaseRuleCode.DISALLOWED_ORIGIN,
            }:
                raise AdminServiceError("ADMIN_VALIDATION_FAILED") from None
            raise AdminServiceError("ADMIN_INVALID_STATE") from None
        except DatabaseUnavailableError:
            raise AdminServiceError("ADMIN_INVALID_STATE") from None


__all__ = ["AdminRepository", "AdminService", "AdminServiceError"]
