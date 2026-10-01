"""FastAPI application: health, state/replay/event feed, world commands and WebSocket."""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import operations, privacy, routes, ws
from .config import Settings
from .contracts import SCHEMA_VERSION
from .contracts.commands import HealthResponse
from .intake.service import IntakeService
from .planning.service import Planner
from .routing.service import RouteService
from .storage.event_store import EventStore


def create_app(
    settings: Settings | None = None,
    store: EventStore | None = None,
    *,
    heartbeat_s: float = 10.0,
    auto_plan: bool = True,
) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # The store opens at startup, not import, so schema export has no side effects.
        app.state.store = store or EventStore(settings.database_path)
        app.state.store.ensure_session()
        app.state.routing = RouteService(
            ors_key=os.environ.get("ORS_API_KEY", "")
            if settings.routing_provider == "ors_directions"
            else None
        )
        app.state.planner = Planner(app.state.store, app.state.routing)
        if auto_plan:
            app.state.planner.start()
        try:
            yield
        finally:
            app.state.planner.close()

    app = FastAPI(
        title="Crisis Command (simulation)",
        version=SCHEMA_VERSION,
        description="Synthetic data and simulated dispatch only. Not an emergency service.",
        lifespan=lifespan,
    )
    # A hosted console on another origin (e.g. Vercel) may call this API only when listed in
    # CRISIS_CORS_ORIGINS (comma-separated). Unset = same-origin only (local dev proxy).
    origins = [o.strip() for o in os.environ.get("CRISIS_CORS_ORIGINS", "").split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_methods=["GET", "POST", "PUT"],
            allow_headers=["Content-Type", "Idempotency-Key"],
            expose_headers=["Idempotent-Replayed", "Retry-After"],
        )
    app.state.settings = settings
    app.state.heartbeat_s = heartbeat_s
    app.state.intake = IntakeService.from_settings(settings.llm_provider)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            mode=settings.mode,
            schema_version=SCHEMA_VERSION,
            routing_provider=settings.routing_provider,
            llm_provider=settings.llm_provider,
            # Model health is the outcome of the latest call, not merely "a model is configured".
            degraded=app.state.intake.degraded
            + (
                ["ROUTING_DEGRADED"]
                if settings.routing_provider == "ors_directions"
                and not os.environ.get("ORS_API_KEY")
                else []
            ),
        )

    routes.install(app)
    app.include_router(ws.router)
    app.include_router(operations.router)
    app.include_router(privacy.router)
    return app


app = create_app()
