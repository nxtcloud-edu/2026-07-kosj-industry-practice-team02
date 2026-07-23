"""Public privacy-first chat endpoint."""

from __future__ import annotations

from typing import Annotated, Protocol
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse

from sejong_ai_api.chat.idempotency import (
    IdempotencyConflictError,
    IdempotencyInProgressError,
)
from sejong_ai_api.chat.service import ChatResult, ChatUnavailableError
from sejong_ai_api.contracts.chat import (
    ChatRequest,
    ChatResponse,
    ServiceUnavailableEnvelope,
)
from sejong_ai_api.contracts.errors import ValidationErrorDetail, ValidationErrorEnvelope
from sejong_ai_api.contracts.health import ServiceUnavailableDetail

RETRY_AFTER_SECONDS = 30


class ChatResponder(Protocol):
    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
        idempotency_key: UUID | None = None,
    ) -> ChatResult: ...


class ClosedChatResponder:
    """Safe default until explicit local dependency composition is supplied."""

    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
        idempotency_key: UUID | None = None,
    ) -> ChatResult:
        del request
        del request_id
        del idempotency_key
        raise ChatUnavailableError()


_DEFAULT_RESPONDER: ChatResponder = ClosedChatResponder()


def get_chat_responder() -> ChatResponder:
    return _DEFAULT_RESPONDER


router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    operation_id="createChatAnswer",
    responses={
        422: {
            "model": ValidationErrorEnvelope,
            "description": "Value-free request validation error.",
        },
        503: {
            "model": ServiceUnavailableEnvelope,
            "description": "No safe grounded response can be produced.",
            "headers": {
                "Retry-After": {
                    "description": "Suggested retry delay in seconds.",
                    "schema": {"type": "integer", "minimum": 1},
                }
            },
        },
    },
)
async def create_chat_answer(
    request: Request,
    payload: ChatRequest,
    responder: Annotated[ChatResponder, Depends(get_chat_responder)],
    idempotency_key: Annotated[UUID | None, Header(alias="Idempotency-Key")] = None,
) -> ChatResult | JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    if not isinstance(request_id, UUID):
        request_id = uuid4()
    try:
        return await responder.answer(
            payload,
            request_id=request_id,
            idempotency_key=idempotency_key,
        )
    except IdempotencyConflictError:
        invalid = ValidationErrorEnvelope(
            error=ValidationErrorDetail(
                code="VALIDATION_ERROR",
                message="입력값을 확인해 주세요.",
                request_id=request_id,
                retryable=False,
            )
        )
        return JSONResponse(
            status_code=422,
            content=invalid.model_dump(mode="json"),
        )
    except (ChatUnavailableError, IdempotencyInProgressError):
        unavailable = ServiceUnavailableEnvelope(
            error=ServiceUnavailableDetail(
                code="SERVICE_UNAVAILABLE",
                message="잠시 후 다시 시도해 주세요.",
                request_id=request_id,
                retryable=True,
            )
        )
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
            content=unavailable.model_dump(mode="json"),
        )


__all__ = ["ChatResponder", "get_chat_responder", "router"]
