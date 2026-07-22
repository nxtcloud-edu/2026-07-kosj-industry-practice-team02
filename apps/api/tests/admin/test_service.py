from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Literal
from uuid import UUID

import pytest
from pydantic import AnyUrl

from sejong_ai_api.admin.service import AdminService, AdminServiceError
from sejong_ai_api.contracts.admin import (
    CandidateReviewRequest,
    FailedQuestion,
    KBCandidateCreateRequest,
    KBCandidateSummary,
    ReasonConfirmationRequest,
)
from sejong_ai_api.db.models import (
    Actor,
    AdminRole,
    CandidateDraft,
    FallbackReason,
    PurgeResult,
)

FAILED_ID = UUID("10000000-0000-4000-8000-000000000001")
CANDIDATE_ID = UUID("20000000-0000-4000-8000-000000000001")
ACTIVATED_ID = UUID("30000000-0000-4000-8000-000000000001")
NOW = datetime(2026, 7, 22, 3, 0, tzinfo=UTC)


def operator(actor_id: str = "OPERATOR-LOCAL-001") -> Actor:
    return Actor(actor_id=actor_id, role=AdminRole.OPERATOR)


def approver(actor_id: str = "PM-LOCAL-001") -> Actor:
    return Actor(actor_id=actor_id, role=AdminRole.APPROVER)


def failed_question(
    *,
    status: Literal["NEW", "REASON_CONFIRMED"] = "NEW",
    reason: Literal[
        "INSUFFICIENT_GROUNDING", "PERSONAL_LOOKUP", "LEGAL_JUDGMENT"
    ] = "INSUFFICIENT_GROUNDING",
) -> FailedQuestion:
    return FailedQuestion(
        id=FAILED_ID,
        masked_question="침대 프레임 수수료를 알려 주세요.",
        intent="BULKY_WASTE",
        fallback_reason=reason,
        candidate_eligible=reason == "INSUFFICIENT_GROUNDING",
        status=status,
        created_at=NOW,
        text_expires_at=NOW + timedelta(days=30),
        text_purged_at=None,
    )


def candidate(
    *,
    status: Literal["DRAFTED", "PENDING_APPROVAL", "APPROVED", "REJECTED"] = "DRAFTED",
    created_by: str = "OPERATOR-LOCAL-001",
) -> KBCandidateSummary:
    reviewed = status in {"APPROVED", "REJECTED"}
    approved = status == "APPROVED"
    return KBCandidateSummary(
        id=CANDIDATE_ID,
        failed_question_id=FAILED_ID,
        title="침대 프레임 배출 안내",
        representative_question="침대 프레임은 어떻게 버리나요?",
        data_origin="OFFICIAL",
        category="BULKY_WASTE",
        answer_summary="신청 후 배출번호를 붙여 배출합니다.",
        procedure_steps=["신청합니다.", "배출합니다."],
        required_documents=[],
        processing_time=None,
        fee="10,000원",
        department="자원순환과",
        source_title="세종특별자치시 대형폐기물 배출 안내",
        source_url=AnyUrl("https://www.sejong.go.kr/example"),
        last_verified_at=date(2026, 7, 19),
        caution=None,
        status=status,
        created_by=created_by,
        reviewed_by="PM-LOCAL-001" if reviewed else None,
        review_comment="공식 출처를 확인했습니다." if reviewed else None,
        approved_at=NOW if approved else None,
        activated_kb_id=ACTIVATED_ID if approved else None,
        created_at=NOW,
        updated_at=NOW,
    )


def create_request(
    *,
    representative_question: str = "침대 프레임은 어떻게 버리나요?",
    answer_summary: str = "신청 후 배출번호를 붙여 배출합니다.",
) -> KBCandidateCreateRequest:
    return KBCandidateCreateRequest(
        failed_question_id=FAILED_ID,
        title="침대 프레임 배출 안내",
        representative_question=representative_question,
        category="BULKY_WASTE",
        answer_summary=answer_summary,
        procedure_steps=["신청합니다.", "배출합니다."],
        required_documents=[],
        processing_time=None,
        fee="10,000원",
        department="자원순환과",
        source_title="세종특별자치시 대형폐기물 배출 안내",
        source_url=AnyUrl("https://www.sejong.go.kr/example"),
        last_verified_at=date(2026, 7, 19),
        caution=None,
    )


class FakeAdminRepository:
    def __init__(self) -> None:
        self.failures = [failed_question()]
        self.candidates = [candidate()]
        self.confirmed: list[tuple[UUID, Actor, FallbackReason]] = []
        self.created: list[CandidateDraft] = []
        self.submitted: list[tuple[UUID, Actor]] = []
        self.approved: list[tuple[UUID, Actor, str]] = []
        self.rejected: list[tuple[UUID, Actor, str]] = []
        self.purge_calls = 0

    async def list_failed_questions(
        self, *, reason: str | None, status: str | None
    ) -> tuple[FailedQuestion, ...]:
        return tuple(
            item
            for item in self.failures
            if (reason is None or item.fallback_reason == reason)
            and (status is None or item.status == status)
        )

    async def get_failed_question(self, failed_question_id: UUID) -> FailedQuestion | None:
        return next((item for item in self.failures if item.id == failed_question_id), None)

    async def list_kb_candidates(self) -> tuple[KBCandidateSummary, ...]:
        return tuple(self.candidates)

    async def get_kb_candidate(self, candidate_id: UUID) -> KBCandidateSummary | None:
        return next((item for item in self.candidates if item.id == candidate_id), None)

    async def purge_expired_failed_question_text(self) -> PurgeResult:
        self.purge_calls += 1
        return PurgeResult(purged_count=0, purged_ids=())

    async def confirm_failed_question_reason(
        self,
        failed_question_id: UUID,
        actor: Actor,
        fallback_reason: FallbackReason,
    ) -> None:
        self.confirmed.append((failed_question_id, actor, fallback_reason))

    async def create_kb_candidate(self, draft: CandidateDraft) -> UUID:
        self.created.append(draft)
        return CANDIDATE_ID

    async def submit_kb_candidate(self, candidate_id: UUID, actor: Actor) -> None:
        self.submitted.append((candidate_id, actor))

    async def approve_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> str:
        self.approved.append((candidate_id, actor, review_comment))
        return "KB-WASTE-03"

    async def reject_kb_candidate(
        self, candidate_id: UUID, actor: Actor, review_comment: str
    ) -> None:
        self.rejected.append((candidate_id, actor, review_comment))


@pytest.mark.asyncio
async def test_lists_and_filters_failed_questions_for_both_admin_roles() -> None:
    repository = FakeAdminRepository()
    service = AdminService(repository)

    result = await service.list_failed_questions(
        approver(), reason="INSUFFICIENT_GROUNDING", status="NEW"
    )

    assert result.total == 1
    assert result.items[0].id == FAILED_ID
    assert repository.purge_calls == 1


@pytest.mark.asyncio
async def test_missing_failed_question_is_value_free_not_found() -> None:
    service = AdminService(FakeAdminRepository())

    with pytest.raises(AdminServiceError) as caught:
        await service.get_failed_question(operator(), UUID(int=0))

    assert caught.value.code == "ADMIN_NOT_FOUND"
    assert str(FAILED_ID) not in str(caught.value)


@pytest.mark.asyncio
async def test_only_operator_can_confirm_reason() -> None:
    service = AdminService(FakeAdminRepository())

    with pytest.raises(AdminServiceError) as caught:
        await service.confirm_reason(
            approver(), FAILED_ID, ReasonConfirmationRequest(reason="INSUFFICIENT_GROUNDING")
        )

    assert caught.value.code == "ADMIN_FORBIDDEN"


@pytest.mark.asyncio
async def test_confirm_reason_delegates_the_typed_existing_capability() -> None:
    repository = FakeAdminRepository()
    service = AdminService(repository)

    result = await service.confirm_reason(
        operator(), FAILED_ID, ReasonConfirmationRequest(reason="INSUFFICIENT_GROUNDING")
    )

    assert result.status == "REASON_CONFIRMED"
    assert repository.confirmed == [(FAILED_ID, operator(), FallbackReason.INSUFFICIENT_GROUNDING)]


@pytest.mark.asyncio
async def test_candidate_create_rechecks_representative_question_for_pii() -> None:
    repository = FakeAdminRepository()
    repository.failures = [failed_question(status="REASON_CONFIRMED")]
    service = AdminService(repository)

    with pytest.raises(AdminServiceError) as caught:
        await service.create_candidate(
            operator(), create_request(representative_question="김철수의 침대를 버려 주세요.")
        )

    assert caught.value.code == "ADMIN_VALIDATION_FAILED"
    assert repository.created == []


@pytest.mark.asyncio
async def test_candidate_create_rechecks_every_candidate_text_field_for_pii() -> None:
    repository = FakeAdminRepository()
    repository.failures = [failed_question(status="REASON_CONFIRMED")]
    service = AdminService(repository)

    with pytest.raises(AdminServiceError) as caught:
        await service.create_candidate(
            operator(), create_request(answer_summary="test-person@example.com으로 연락하세요.")
        )

    assert caught.value.code == "ADMIN_VALIDATION_FAILED"
    assert repository.created == []


@pytest.mark.asyncio
async def test_candidate_create_uses_official_origin_and_operator_identity() -> None:
    repository = FakeAdminRepository()
    repository.failures = [failed_question(status="REASON_CONFIRMED")]
    service = AdminService(repository)

    result = await service.create_candidate(operator(), create_request())

    assert result.status == "DRAFTED"
    assert result.id == CANDIDATE_ID
    assert len(repository.created) == 1
    assert repository.created[0].actor == operator()
    assert repository.created[0].data_origin.value == "OFFICIAL"


@pytest.mark.asyncio
async def test_only_candidate_creator_can_submit_draft() -> None:
    repository = FakeAdminRepository()
    service = AdminService(repository)

    with pytest.raises(AdminServiceError) as caught:
        await service.submit_candidate(operator("OTHER-OPERATOR"), CANDIDATE_ID)

    assert caught.value.code == "ADMIN_FORBIDDEN"
    assert repository.submitted == []


@pytest.mark.asyncio
async def test_creator_cannot_review_own_candidate() -> None:
    repository = FakeAdminRepository()
    repository.candidates = [candidate(status="PENDING_APPROVAL", created_by="PM-LOCAL-001")]
    service = AdminService(repository)

    with pytest.raises(AdminServiceError) as caught:
        await service.review_candidate(
            approver(),
            CANDIDATE_ID,
            CandidateReviewRequest(decision="APPROVED", review_comment="출처를 확인했습니다."),
        )

    assert caught.value.code == "ADMIN_FORBIDDEN"
    assert repository.approved == []


@pytest.mark.asyncio
@pytest.mark.parametrize("decision", ["APPROVED", "REJECTED"])
async def test_different_approver_can_apply_both_review_outcomes(decision: str) -> None:
    repository = FakeAdminRepository()
    repository.candidates = [candidate(status="PENDING_APPROVAL")]
    service = AdminService(repository)

    result = await service.review_candidate(
        approver(),
        CANDIDATE_ID,
        CandidateReviewRequest(
            decision=decision,  # type: ignore[arg-type]
            review_comment="공식 출처를 확인했습니다.",
        ),
    )

    assert result.status == decision
    if decision == "APPROVED":
        assert len(repository.approved) == 1
        assert repository.rejected == []
    else:
        assert len(repository.rejected) == 1
        assert repository.approved == []
