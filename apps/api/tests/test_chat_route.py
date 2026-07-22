from __future__ import annotations

import io
import json
import logging
from uuid import UUID

from fastapi.testclient import TestClient

from sejong_ai_api.chat.response import build_fallback_response
from sejong_ai_api.chat.service import ChatResult, ChatUnavailableError
from sejong_ai_api.contracts.chat import ChatRequest
from sejong_ai_api.core.logging import SafeRequestJsonFormatter
from sejong_ai_api.db.models import Intent
from sejong_ai_api.main import create_app

REQUEST_ID = UUID("11111111-1111-4111-8111-111111111111")


class FakeResponder:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.unavailable = unavailable
        self.requests: list[ChatRequest] = []
        self.request_ids: list[UUID | None] = []

    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
    ) -> ChatResult:
        self.requests.append(request)
        self.request_ids.append(request_id)
        if self.unavailable:
            raise ChatUnavailableError()
        return build_fallback_response(
            request_id=request_id if request_id is not None else REQUEST_ID,
            intent=Intent.UNKNOWN,
            reason="PRIVACY_UNRESOLVED",
            office=None,
        )


def safe_logger() -> tuple[logging.Logger, io.StringIO]:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(SafeRequestJsonFormatter())
    logger = logging.Logger("chat-route-test", level=logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    return logger, stream


def test_chat_route_returns_the_typed_policy_result() -> None:
    responder = FakeResponder()

    with TestClient(
        create_app(chat_responder=responder, request_id_factory=lambda: REQUEST_ID)
    ) as client:
        response = client.post("/api/v1/chat", json={"question": "김철수"})

    assert response.status_code == 200
    assert response.json()["request_id"] == str(REQUEST_ID)
    assert response.json()["answer_status"] == "FALLBACK"
    assert response.json()["fallback"]["reason"] == "PRIVACY_UNRESOLVED"
    assert len(responder.requests) == 1
    assert responder.request_ids == [REQUEST_ID]


def test_unavailable_chat_route_returns_the_exact_retryable_envelope() -> None:
    responder = FakeResponder(unavailable=True)

    with TestClient(
        create_app(chat_responder=responder, request_id_factory=lambda: REQUEST_ID)
    ) as client:
        response = client.post(
            "/api/v1/chat",
            json={"question": "대형폐기물 배출 방법"},
        )

    assert response.status_code == 503
    assert response.headers["Retry-After"] == "30"
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert body["error"]["message"] == "잠시 후 다시 시도해 주세요."
    assert body["error"]["retryable"] is True
    assert body["error"]["request_id"] == str(REQUEST_ID)


def test_default_chat_dependency_is_closed_until_local_composition_is_injected() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/chat",
            json={"question": "대형폐기물 배출 방법"},
        )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"


def test_invalid_chat_request_is_value_free_in_body_and_request_log() -> None:
    sentinel = "RAW-QUESTION-MUST-NOT-ECHO"
    logger, stream = safe_logger()

    with TestClient(
        create_app(
            chat_responder=FakeResponder(),
            request_logger=logger,
            request_id_factory=lambda: REQUEST_ID,
        )
    ) as client:
        response = client.post(
            "/api/v1/chat",
            json={"question": sentinel, "unexpected": sentinel},
        )

    assert response.status_code == 422
    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "입력값을 확인해 주세요.",
            "request_id": response.json()["error"]["request_id"],
            "retryable": False,
        }
    }
    assert response.json()["error"]["request_id"] == str(REQUEST_ID)
    assert json.loads(stream.getvalue())["request_id"] == str(REQUEST_ID)
    serialized = json.dumps(response.json(), ensure_ascii=False) + stream.getvalue()
    assert sentinel not in serialized
    assert "unexpected" not in serialized


def test_generated_fastapi_openapi_tracks_chat_response_and_safe_errors() -> None:
    operation = create_app().openapi()["paths"]["/api/v1/chat"]["post"]

    assert operation["operationId"] == "createChatAnswer"
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert operation["responses"]["422"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ValidationErrorEnvelope"
    }
    assert operation["responses"]["503"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ServiceUnavailableEnvelope"
    }
