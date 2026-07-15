"""Typed runtime models for the approved chat contract intersection."""

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AnyUrl, ConfigDict, Field, TypeAdapter, field_validator

from sejong_ai_api.contracts.health import (
    ServiceUnavailableEnvelope,
    StrictPublicModel,
)

type Intent = Literal[
    "MOVE_IN_RESIDENT_REGISTRATION",
    "CERTIFICATE_ISSUANCE",
    "BULKY_WASTE",
    "LOCAL_TAX_GENERAL",
    "OUT_OF_SCOPE",
    "UNKNOWN",
]
type FallbackReason = Literal[
    "INSUFFICIENT_GROUNDING",
    "PERSONAL_LOOKUP",
    "LEGAL_JUDGMENT",
    "OUT_OF_SCOPE",
]
type Region = Literal["아름동", "도담동", "조치원읍"]
type ContextToken = Annotated[str, Field(min_length=1, max_length=2048)]


class ChatRequest(StrictPublicModel):
    question: Annotated[str, Field(min_length=1, max_length=1000)]
    context_token: ContextToken | None = None
    selected_region: Region | None = None
    simple_language: bool = False


class Source(StrictPublicModel):
    source_id: str
    title: str
    url: AnyUrl
    last_verified_at: date
    used_fields: list[str] = Field(default_factory=list)


class Office(StrictPublicModel):
    """OpenAPI intentionally permits forward-compatible office fields."""

    model_config = ConfigDict(extra="allow", strict=True)

    id: str
    region: str
    office_name: str
    address: str
    phone: str
    opening_hours: str | None = None
    map_url: AnyUrl | None = None
    source_title: str
    source_url: AnyUrl | None = None
    last_verified_at: date

    @field_validator("source_url", mode="before")
    @classmethod
    def reject_explicit_null_source_url(cls, value: object) -> object:
        if value is None:
            raise ValueError("source_url may be omitted but cannot be null")
        return value


class Fallback(StrictPublicModel):
    reason: FallbackReason
    title: str
    message: str
    next_actions: list[str] = Field(default_factory=list)
    candidate_eligible: bool
    office: Office | None = None


class ChatResponseBase(StrictPublicModel):
    request_id: UUID
    intent: Intent
    confidence: Annotated[float | None, Field(ge=0, le=1)] = None
    summary: str | None = None
    procedure_steps: list[str] = Field(default_factory=list)
    required_documents: list[str] = Field(default_factory=list)
    processing_time: str | None = None
    fee: str | None = None
    department: str | None = None
    followup_options: list[str] = Field(default_factory=list)
    fallback: Fallback | None = None


class SuccessResponse(ChatResponseBase):
    answer_status: Literal["SUCCESS"]
    sources: Annotated[list[Source], Field(min_length=1)]
    context_token: ContextToken | None


class FollowupResponse(ChatResponseBase):
    answer_status: Literal["FOLLOWUP"]
    sources: list[Source]
    context_token: ContextToken | None


class FallbackResponse(ChatResponseBase):
    answer_status: Literal["FALLBACK"]
    sources: list[Source]
    context_token: None


type ChatResponse = Annotated[
    SuccessResponse | FollowupResponse | FallbackResponse,
    Field(discriminator="answer_status"),
]
CHAT_RESPONSE_ADAPTER: TypeAdapter[ChatResponse] = TypeAdapter(ChatResponse)


__all__ = [
    "CHAT_RESPONSE_ADAPTER",
    "ChatRequest",
    "ChatResponse",
    "FallbackResponse",
    "FollowupResponse",
    "Office",
    "ServiceUnavailableEnvelope",
    "Source",
    "SuccessResponse",
]
