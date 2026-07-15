"""FastAPI application factory."""

import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi import FastAPI

from sejong_ai_api.api.health import ReadinessProbe, get_readiness_probe, router
from sejong_ai_api.core.logging import (
    SafeRequestLoggingMiddleware,
    configure_uvicorn_log_safety,
    get_safe_request_logger,
)


def create_app(
    *,
    readiness_probe: ReadinessProbe | None = None,
    request_logger: logging.Logger | None = None,
    request_id_factory: Callable[[], UUID] = uuid4,
) -> FastAPI:
    """Build an import-safe API application with an optional readiness seam."""
    configure_uvicorn_log_safety()
    application = FastAPI(title="Sejong Civil AI API", version="2.0.1-draft")
    application.include_router(router)
    application.add_middleware(
        SafeRequestLoggingMiddleware,
        logger=request_logger if request_logger is not None else get_safe_request_logger(),
        request_id_factory=request_id_factory,
    )

    if readiness_probe is not None:
        injected_probe = readiness_probe

        def provide_injected_readiness_probe() -> ReadinessProbe:
            return injected_probe

        application.dependency_overrides[get_readiness_probe] = provide_injected_readiness_probe

    return application


app = create_app()
