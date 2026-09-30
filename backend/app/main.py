"""FastAPI application. CC-02 provides only ``GET /health``; later tasks add the API."""

from __future__ import annotations

from fastapi import FastAPI

from .config import Settings
from .contracts import SCHEMA_VERSION
from .contracts.commands import HealthResponse


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="Crisis Command (simulation)",
        version=SCHEMA_VERSION,
        description="Synthetic data and simulated dispatch only. Not an emergency service.",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            mode=settings.mode,
            schema_version=SCHEMA_VERSION,
            routing_provider=settings.routing_provider,
            llm_provider=settings.llm_provider,
            degraded=[],
        )

    return app


app = create_app()
