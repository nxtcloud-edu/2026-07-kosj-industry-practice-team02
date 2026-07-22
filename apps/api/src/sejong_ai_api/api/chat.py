"""Public privacy-first chat endpoint."""

from __future__ import annotations

from typing import Annotated, Protocol
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from sejong_ai_api.chat.service import ChatResult, ChatUnavailableError
from sejong_ai_api.contracts.chat import (
    ChatRequest,
    ChatResponse,
    ServiceUnavailableEnvelope,
)
from sejong_ai_api.contracts.errors import ValidationErrorEnvelope
from sejong_ai_api.contracts.health import ServiceUnavailableDetail

RETRY_AFTER_SECONDS = 30


class ChatResponder(Protocol):
    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
    ) -> ChatResult: ...


class ClosedChatResponder:
    """Safe default until explicit local dependency composition is supplied."""

    async def answer(
        self,
        request: ChatRequest,
        *,
        request_id: UUID | None = None,
    ) -> ChatResult:
        del request
        del request_id
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
) -> ChatResult | JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    if not isinstance(request_id, UUID):
        request_id = uuid4()
    try:
        return await responder.answer(payload, request_id=request_id)
    except ChatUnavailableError:
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
