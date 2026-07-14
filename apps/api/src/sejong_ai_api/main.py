"""FastAPI application factory."""

from fastapi import FastAPI

from sejong_ai_api.api.health import ReadinessProbe, get_readiness_probe, router


def create_app(*, readiness_probe: ReadinessProbe | None = None) -> FastAPI:
    """Build an import-safe API application with an optional readiness seam."""
    application = FastAPI(title="Sejong Civil AI API", version="2.0.0-draft")
    application.include_router(router)

    if readiness_probe is not None:
        injected_probe = readiness_probe

        def provide_injected_readiness_probe() -> ReadinessProbe:
            return injected_probe

        application.dependency_overrides[get_readiness_probe] = provide_injected_readiness_probe

    return application


app = create_app()
