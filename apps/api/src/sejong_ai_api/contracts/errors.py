"""Closed public request-error envelopes that never echo input values."""

from typing import Literal
from uuid import UUID

from pydantic import field_validator

from sejong_ai_api.contracts.health import StrictPublicModel


class ValidationErrorDetail(StrictPublicModel):
    code: Literal["VALIDATION_ERROR"]
    message: Literal["입력값을 확인해 주세요."]
    request_id: UUID
    retryable: Literal[False]

    @field_validator("retryable", mode="before")
    @classmethod
    def require_boolean_false(cls, value: object) -> object:
        if value is not False:
            raise ValueError("retryable must be the JSON boolean false")
        return value


class ValidationErrorEnvelope(StrictPublicModel):
    error: ValidationErrorDetail


__all__ = ["ValidationErrorDetail", "ValidationErrorEnvelope"]
