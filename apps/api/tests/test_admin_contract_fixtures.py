import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

import sejong_ai_api.contracts.admin as admin_contracts

FIXTURE_ROOT = Path(__file__).parents[3] / "contracts" / "fixtures" / "admin"


def read_fixture(name: str) -> dict[str, Any]:
    text = (FIXTURE_ROOT / name).read_text(encoding="utf-8")
    payload: dict[str, Any] = json.loads(text)
    return payload


@pytest.mark.parametrize(
    ("fixture", "model_name", "valid"),
    [
        ("valid-failed-question-list.json", "FailedQuestionListResponse", True),
        ("valid-failed-question-detail.json", "FailedQuestionDetailResponse", True),
        ("valid-reason-confirmation.json", "ReasonConfirmationResponse", True),
        ("valid-candidate-list.json", "KBCandidateListResponse", True),
        ("valid-candidate-create.json", "KBCandidateCreateResponse", True),
        ("valid-candidate-submit.json", "KBCandidateSubmitResponse", True),
        ("valid-candidate-review.json", "KBCandidateReviewResponse", True),
        ("invalid-list-missing-total.json", "FailedQuestionListResponse", False),
        ("invalid-review-status.json", "KBCandidateReviewResponse", False),
        ("valid-admin-error.json", "AdminErrorEnvelope", True),
        ("invalid-admin-error-echo.json", "AdminErrorEnvelope", False),
        ("invalid-admin-error-message.json", "AdminErrorEnvelope", False),
        ("invalid-failed-candidate-eligibility.json", "FailedQuestionListResponse", False),
        ("invalid-failed-null-without-purge.json", "FailedQuestionDetailResponse", False),
        ("invalid-failed-purge-before-expiry.json", "FailedQuestionDetailResponse", False),
        ("invalid-failed-text-with-purge.json", "FailedQuestionDetailResponse", False),
        ("invalid-failed-wrong-expiry.json", "FailedQuestionDetailResponse", False),
        ("invalid-candidate-approved-incomplete.json", "KBCandidateListResponse", False),
        ("invalid-candidate-self-review.json", "KBCandidateListResponse", False),
        ("invalid-candidate-pending-reviewed.json", "KBCandidateListResponse", False),
        ("invalid-candidate-rejected-activated.json", "KBCandidateListResponse", False),
        ("invalid-candidate-approved-mock.json", "KBCandidateListResponse", False),
    ],
)
def test_admin_contracts_consume_shared_fixtures(
    fixture: str, model_name: str, valid: bool
) -> None:
    model = getattr(admin_contracts, model_name)
    payload = read_fixture(fixture)
    if valid:
        model.model_validate_json(json.dumps(payload, ensure_ascii=False), strict=True)
    else:
        with pytest.raises(ValidationError):
            model.model_validate_json(json.dumps(payload, ensure_ascii=False), strict=True)


def test_admin_envelopes_are_closed_and_do_not_echo_question_or_answer_snapshots() -> None:
    payload = read_fixture("valid-candidate-review.json")
    payload["masked_question"] = "시연용 샘플 금지 필드"
    with pytest.raises(ValidationError):
        admin_contracts.KBCandidateReviewResponse.model_validate_json(
            json.dumps(payload, ensure_ascii=False), strict=True
        )


@pytest.mark.parametrize(
    "url", ["javascript:alert(1)", "data:text/html,test", "http://example.invalid"]
)
def test_admin_candidate_contract_rejects_non_https_source_url(url: str) -> None:
    payload = read_fixture("valid-candidate-list.json")
    payload["items"][0]["source_url"] = url
    with pytest.raises(ValidationError):
        admin_contracts.KBCandidateListResponse.model_validate_json(
            json.dumps(payload, ensure_ascii=False), strict=True
        )


def test_admin_request_models_reject_broad_intents_and_unbounded_review_copy() -> None:
    candidate_payload = {
        "failed_question_id": "10000000-0000-4000-8000-000000000001",
        "title": "시연용 샘플 후보",
        "representative_question": "시연용 샘플 질문",
        "category": "OUT_OF_SCOPE",
        "answer_summary": "시연용 샘플 답변",
        "department": "시연용 샘플 부서",
        "source_title": "시연용 샘플 출처",
        "source_url": "https://example.invalid/admin/source",
        "last_verified_at": "2026-07-15",
    }
    with pytest.raises(ValidationError):
        admin_contracts.KBCandidateCreateRequest.model_validate(candidate_payload)
    with pytest.raises(ValidationError):
        admin_contracts.CandidateReviewRequest.model_validate(
            {"decision": "APPROVED", "review_comment": " "}
        )
    with pytest.raises(ValidationError):
        admin_contracts.ReasonConfirmationRequest.model_validate({"reason": "OUT_OF_SCOPE"})
