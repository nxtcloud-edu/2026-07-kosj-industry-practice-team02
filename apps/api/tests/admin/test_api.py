from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from sejong_ai_api.admin.service import AdminServiceError
from sejong_ai_api.api.admin import (
    get_admin_enabled,
    get_admin_service,
    router,
)
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
    ReasonConfirmationRequest,
    ReasonConfirmationResponse,
)
from sejong_ai_api.db.models import Actor, AdminRole

REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")
FAILED_ID = UUID("10000000-0000-4000-8000-000000000001")
CANDIDATE_ID = UUID("20000000-0000-4000-8000-000000000001")
NOW = datetime(2026, 7, 22, 3, 0, tzinfo=UTC)


def failure() -> FailedQuestion:
    return FailedQuestion(
        id=FAILED_ID,
        masked_question="침대 프레임 수수료를 알려 주세요.",
        intent="BULKY_WASTE",
        fallback_reason="INSUFFICIENT_GROUNDING",
        candidate_eligible=True,
        status="NEW",
        created_at=NOW,
        text_expires_at=NOW + timedelta(days=30),
        text_purged_at=None,
    )


class RouteService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Actor]] = []
        self.error: AdminServiceError | None = None

    def _record(self, name: str, actor: Actor) -> None:
        self.calls.append((name, actor))
        if self.error is not None:
            raise self.error

    async def list_failed_questions(
        self, actor: Actor, *, reason: str | None, status: str | None
    ) -> FailedQuestionListResponse:
        del reason, status
        self._record("list_failed_questions", actor)
        return FailedQuestionListResponse(items=[failure()], total=1)

    async def get_failed_question(
        self, actor: Actor, failed_question_id: UUID
    ) -> FailedQuestionDetailResponse:
        del failed_question_id
        self._record("get_failed_question", actor)
        return FailedQuestionDetailResponse(item=failure())

    async def confirm_reason(
        self,
        actor: Actor,
        failed_question_id: UUID,
        payload: ReasonConfirmationRequest,
    ) -> ReasonConfirmationResponse:
        del failed_question_id, payload
        self._record("confirm_reason", actor)
        return ReasonConfirmationResponse(id=FAILED_ID, status="REASON_CONFIRMED")

    async def list_candidates(self, actor: Actor) -> KBCandidateListResponse:
        self._record("list_candidates", actor)
        return KBCandidateListResponse(items=[], total=0)

    async def create_candidate(
        self, actor: Actor, payload: KBCandidateCreateRequest
    ) -> KBCandidateCreateResponse:
        del payload
        self._record("create_candidate", actor)
        return KBCandidateCreateResponse(id=CANDIDATE_ID, status="DRAFTED")

    async def submit_candidate(self, actor: Actor, candidate_id: UUID) -> KBCandidateSubmitResponse:
        del candidate_id
        self._record("submit_candidate", actor)
        return KBCandidateSubmitResponse(id=CANDIDATE_ID, status="PENDING_APPROVAL")

    async def review_candidate(
        self,
        actor: Actor,
        candidate_id: UUID,
        payload: CandidateReviewRequest,
    ) -> KBCandidateReviewResponse:
        del candidate_id
        self._record("review_candidate", actor)
        return KBCandidateReviewResponse(id=CANDIDATE_ID, status=payload.decision)


def application(*, enabled: bool, service: RouteService | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(router)

    @app.middleware("http")
    async def attach_request_id(request: Request, call_next):  # type: ignore[no-untyped-def]
        request.state.request_id = REQUEST_ID
        return await call_next(request)

    app.dependency_overrides[get_admin_enabled] = lambda: enabled
    if service is not None:
        app.dependency_overrides[get_admin_service] = lambda: service
    return app


def headers(*, actor_id: str = "OPERATOR-LOCAL-001", role: str = "OPERATOR") -> dict[str, str]:
    return {"X-Demo-Actor-Id": actor_id, "X-Demo-Role": role}


def test_admin_routes_are_disabled_by_default_with_exact_value_free_error() -> None:
    with TestClient(application(enabled=False)) as client:
        response = client.get("/api/v1/admin/failed-questions", headers=headers())

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "ADMIN_ROUTE_DISABLED",
            "message": "관리자 기능을 사용할 수 없습니다.",
            "request_id": str(REQUEST_ID),
            "retryable": False,
        }
    }


def test_enabled_admin_route_requires_both_demo_actor_headers() -> None:
    with TestClient(application(enabled=True, service=RouteService())) as client:
        response = client.get("/api/v1/admin/failed-questions")

    assert response.status_code == 422


def test_enabled_admin_route_rejects_an_unapproved_demo_actor_identity() -> None:
    service = RouteService()

    with TestClient(application(enabled=True, service=service)) as client:
        response = client.get(
            "/api/v1/admin/failed-questions",
            headers=headers(actor_id="CALLER-CHOSEN-001", role="OPERATOR"),
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ADMIN_FORBIDDEN"
    assert service.calls == []


def test_failed_question_list_forwards_typed_filters_and_actor() -> None:
    service = RouteService()

    with TestClient(application(enabled=True, service=service)) as client:
        response = client.get(
            "/api/v1/admin/failed-questions?reason=INSUFFICIENT_GROUNDING&status=NEW",
            headers=headers(role="APPROVER", actor_id="PM-LOCAL-001"),
        )

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert service.calls == [("list_failed_questions", Actor("PM-LOCAL-001", AdminRole.APPROVER))]


def test_operator_reason_confirmation_is_wired_to_the_service() -> None:
    service = RouteService()

    with TestClient(application(enabled=True, service=service)) as client:
        response = client.patch(
            f"/api/v1/admin/failed-questions/{FAILED_ID}/reason",
            headers=headers(),
            json={"reason": "INSUFFICIENT_GROUNDING"},
        )

    assert response.status_code == 200
    assert response.json() == {"id": str(FAILED_ID), "status": "REASON_CONFIRMED"}
    assert service.calls[0][0] == "confirm_reason"


def test_service_errors_map_to_exact_admin_envelopes_without_exception_text() -> None:
    service = RouteService()
    service.error = AdminServiceError("ADMIN_INVALID_STATE")

    with TestClient(application(enabled=True, service=service)) as client:
        response = client.post(
            f"/api/v1/admin/kb-candidates/{CANDIDATE_ID}/submit",
            headers=headers(),
        )

    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "ADMIN_INVALID_STATE",
        "message": "현재 상태에서는 이 작업을 수행할 수 없습니다.",
        "request_id": str(REQUEST_ID),
        "retryable": False,
    }
    assert "ADMIN_INVALID_STATE" not in response.text.replace('"code":"ADMIN_INVALID_STATE"', "")
