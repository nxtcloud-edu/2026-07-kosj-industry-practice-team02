import json
from uuid import UUID

import pytest
from pydantic import ValidationError

from sejong_ai_api.contracts.errors import (
    ValidationErrorDetail,
    ValidationErrorEnvelope,
)

REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")


def test_validation_error_contract_is_closed_and_value_free() -> None:
    envelope = ValidationErrorEnvelope(
        error=ValidationErrorDetail(
            code="VALIDATION_ERROR",
            message="입력값을 확인해 주세요.",
            request_id=REQUEST_ID,
            retryable=False,
        )
    )

    assert envelope.model_dump(mode="json") == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "입력값을 확인해 주세요.",
            "request_id": str(REQUEST_ID),
            "retryable": False,
        }
    }

    for invalid in (
        {"error": {**envelope.model_dump(mode="json")["error"], "input": "raw"}},
        {"error": {**envelope.model_dump(mode="json")["error"], "message": "raw"}},
        {"error": {**envelope.model_dump(mode="json")["error"], "retryable": 0}},
    ):
        with pytest.raises(ValidationError):
            ValidationErrorEnvelope.model_validate_json(json.dumps(invalid))
