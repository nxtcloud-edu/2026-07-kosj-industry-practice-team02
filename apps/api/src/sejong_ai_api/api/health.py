"""Process health and dependency readiness endpoints."""

from typing import Annotated, Protocol
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from sejong_ai_api.contracts.health import (
    HealthResponse,
    ReadyResponse,
    ServiceUnavailableDetail,
    ServiceUnavailableEnvelope,
)

RETRY_AFTER_SECONDS = 30


class ReadinessProbe(Protocol):
    """Boundary for checking required dependencies without coupling this router to them."""

    def is_ready(self) -> bool:
        """Return whether all required dependencies and approved seed data are ready."""
        ...


class PreDatabaseReadinessProbe:
    """Safe default until the database and required approved seed are implemented."""

    def is_ready(self) -> bool:
        return False


_DEFAULT_READINESS_PROBE: ReadinessProbe = PreDatabaseReadinessProbe()


def get_readiness_probe() -> ReadinessProbe:
    """Provide the current readiness policy for FastAPI dependency injection."""
    return _DEFAULT_READINESS_PROBE


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Report process liveness without consulting external dependencies."""
    return HealthResponse()


@router.get(
    "/ready",
    response_model=ReadyResponse,
    responses={503: {"model": ServiceUnavailableEnvelope}},
)
def get_readiness(
    probe: Annotated[ReadinessProbe, Depends(get_readiness_probe)],
) -> ReadyResponse | JSONResponse:
    """Report whether required dependencies and approved seed data are usable."""
    if probe.is_ready():
        return ReadyResponse()

    unavailable = ServiceUnavailableEnvelope(
        error=ServiceUnavailableDetail(
            code="SERVICE_UNAVAILABLE",
            message="잠시 후 다시 시도해 주세요.",
            request_id=uuid4(),
            retryable=True,
        )
    )
    return JSONResponse(
        status_code=503,
        headers={"Retry-After": str(RETRY_AFTER_SECONDS)},
        content=unavailable.model_dump(mode="json"),
    )
