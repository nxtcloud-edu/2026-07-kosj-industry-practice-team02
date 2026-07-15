"""Public response models for health and readiness."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictPublicModel(BaseModel):
    """Reject undeclared public response fields."""

    model_config = ConfigDict(extra="forbid", strict=True)


class HealthResponse(StrictPublicModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(StrictPublicModel):
    status: Literal["ready"] = "ready"


class ServiceUnavailableDetail(StrictPublicModel):
    code: Literal["SERVICE_UNAVAILABLE"]
    message: Annotated[str, Field(min_length=1, max_length=200)]
    request_id: UUID
    retryable: Literal[True]

    @field_validator("retryable", mode="before")
    @classmethod
    def require_boolean_true(cls, value: object) -> object:
        if value is not True:
            raise ValueError("retryable must be the JSON boolean true")
        return value


class ServiceUnavailableEnvelope(StrictPublicModel):
    error: ServiceUnavailableDetail
