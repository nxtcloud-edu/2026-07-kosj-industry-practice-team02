import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from sejong_ai_api.contracts.chat import (
    CHAT_RESPONSE_ADAPTER,
    ChatRequest,
    Office,
)
from sejong_ai_api.contracts.chat import (
    ServiceUnavailableEnvelope as ChatServiceUnavailableEnvelope,
)
from sejong_ai_api.contracts.health import ServiceUnavailableEnvelope

FIXTURE_ROOT = Path(__file__).parents[3] / "contracts" / "fixtures"


def read_fixture_text(relative_path: str) -> str:
    payload = (FIXTURE_ROOT / relative_path).read_text(encoding="utf-8")
    assert "시연용 샘플" in payload
    return payload


def read_fixture(relative_path: str) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(read_fixture_text(relative_path))
    return payload


@pytest.mark.parametrize(
    ("fixture", "valid"),
    [
        ("valid-first-request.json", True),
        ("valid-null-context.json", True),
        ("invalid-session-id.json", False),
    ],
)
def test_chat_request_consumes_shared_fixtures(fixture: str, valid: bool) -> None:
    payload = read_fixture_text(f"chat-request/{fixture}")

    if valid:
        ChatRequest.model_validate_json(payload)
    else:
        with pytest.raises(ValidationError):
            ChatRequest.model_validate_json(payload)


@pytest.mark.parametrize(
    ("fixture", "valid"),
    [
        ("valid-success.json", True),
        ("invalid-success-empty-sources.json", False),
        ("valid-followup.json", True),
        ("valid-fallback-no-office.json", True),
        ("valid-fallback-office.json", True),
        ("invalid-fallback-context.json", False),
        ("invalid-missing-context.json", False),
        ("invalid-session-id.json", False),
        ("invalid-office-missing-id.json", False),
    ],
)
def test_chat_response_consumes_shared_fixtures(fixture: str, valid: bool) -> None:
    payload = read_fixture_text(f"chat-response/{fixture}")

    if valid:
        CHAT_RESPONSE_ADAPTER.validate_json(payload, strict=True)
    else:
        with pytest.raises(ValidationError):
            CHAT_RESPONSE_ADAPTER.validate_json(payload, strict=True)


@pytest.mark.parametrize(
    ("fixture", "valid"),
    [
        ("valid-service-unavailable.json", True),
        ("invalid-code.json", False),
        ("invalid-extra-property.json", False),
        ("invalid-request-id.json", False),
    ],
)
def test_service_unavailable_consumes_shared_fixtures(fixture: str, valid: bool) -> None:
    payload = read_fixture_text(f"errors/{fixture}")

    if valid:
        ServiceUnavailableEnvelope.model_validate_json(payload)
    else:
        with pytest.raises(ValidationError):
            ServiceUnavailableEnvelope.model_validate_json(payload)


def test_chat_contract_reuses_the_existing_service_unavailable_model() -> None:
    assert ChatServiceUnavailableEnvelope is ServiceUnavailableEnvelope


def test_chat_request_rejects_integer_boolean_coercion() -> None:
    request = read_fixture("chat-request/valid-null-context.json")
    request["simple_language"] = 1
    with pytest.raises(ValidationError):
        ChatRequest.model_validate_json(json.dumps(request, ensure_ascii=False))


def test_chat_response_rejects_string_number_coercion() -> None:
    response = read_fixture("chat-response/valid-success.json")
    response["confidence"] = "0.5"
    with pytest.raises(ValidationError):
        CHAT_RESPONSE_ADAPTER.validate_json(json.dumps(response, ensure_ascii=False), strict=True)


def test_service_unavailable_rejects_integer_literal_coercion() -> None:
    unavailable = read_fixture("errors/valid-service-unavailable.json")
    unavailable["error"]["retryable"] = 1
    with pytest.raises(ValidationError):
        ServiceUnavailableEnvelope.model_validate_json(json.dumps(unavailable, ensure_ascii=False))


def test_office_allows_future_fields_but_rejects_explicit_null_source_url() -> None:
    payload = read_fixture("chat-response/valid-fallback-office.json")
    office_payload = deepcopy(payload["fallback"]["office"])
    office_payload["future_office_field"] = "시연용 샘플 확장 필드"

    office = Office.model_validate_json(json.dumps(office_payload, ensure_ascii=False))
    assert office.__pydantic_extra__ == {"future_office_field": "시연용 샘플 확장 필드"}

    office_payload["source_url"] = None
    with pytest.raises(ValidationError):
        Office.model_validate_json(json.dumps(office_payload, ensure_ascii=False))
