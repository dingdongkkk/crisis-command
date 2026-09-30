"""FastAPI application: health, state/replay/event feed, world commands and WebSocket."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api import routes, ws
from .config import Settings
from .contracts import SCHEMA_VERSION
from .contracts.commands import HealthResponse
from .storage.event_store import EventStore


def create_app(
    settings: Settings | None = None,
    store: EventStore | None = None,
    *,
    heartbeat_s: float = 10.0,
) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # The store opens at startup, not import, so schema export has no side effects.
        app.state.store = store or EventStore(settings.database_path)
        app.state.store.ensure_session()
        yield

    app = FastAPI(
        title="Crisis Command (simulation)",
        version=SCHEMA_VERSION,
        description="Synthetic data and simulated dispatch only. Not an emergency service.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.heartbeat_s = heartbeat_s

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

    routes.install(app)
    app.include_router(ws.router)
    return app


app = create_app()
