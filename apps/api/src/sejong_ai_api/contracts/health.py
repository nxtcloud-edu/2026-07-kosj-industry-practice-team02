"""Public response models for health and readiness."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class StrictPublicModel(BaseModel):
    """Reject undeclared public response fields."""

    model_config = ConfigDict(extra="forbid")


class HealthResponse(StrictPublicModel):
    status: Literal["ok"] = "ok"


class ReadyResponse(StrictPublicModel):
    status: Literal["ready"] = "ready"


class ServiceUnavailableDetail(StrictPublicModel):
    code: Literal["SERVICE_UNAVAILABLE"]
    message: Annotated[str, Field(min_length=1, max_length=200)]
    request_id: UUID
    retryable: Literal[True]


class ServiceUnavailableEnvelope(StrictPublicModel):
    error: ServiceUnavailableDetail
