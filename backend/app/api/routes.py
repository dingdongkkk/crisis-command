"""HTTP routes for state, replay, the event feed and CC-03 world commands (0001, 0005, 0008).

Later tasks add reports/intake (CC-06), planning and approvals (CC-05/CC-08) and the
scenario runner (CC-10) on the same store and receipt machinery.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from fastapi import APIRouter, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.contracts.commands import (
    DemoResetCommand,
    DemoResetResult,
    FloodAccepted,
    FloodEventCommand,
    RouteCandidates,
    UnitStatusAccepted,
    UnitStatusCommand,
)
from app.contracts.common import Problem
from app.contracts.entities import Route
from app.contracts.events import (
    EnvelopeBase,
    EventEnvelope,
    FloodZoneUpdatedPayload,
    UnitStatusChangedPayload,
)
from app.contracts.state import StateSnapshot
from app.domain.commands import DomainError, flood_update, unit_status
from app.routing.service import RouteService
from app.storage.event_store import CommandResult, DatabaseBusyError, Decision, EventStore, problem

OPERATOR = {"kind": "operator", "id": "op_demo_1"}
"""Synthetic operator identity. The MVP has no authentication (stated limitation)."""

UUID4 = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
PROBLEM_RESPONSES: dict[int | str, dict[str, Any]] = {
    code: {"model": Problem} for code in (400, 404, 409, 410, 422, 503)
}

router = APIRouter()
IdempotencyKey = Annotated[str | None, Header(alias="Idempotency-Key")]


def problem_response(error: DomainError, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse(
        problem(error),
        status_code=error.status,
        headers=headers,
        media_type="application/problem+json",
    )


def _result_response(result: CommandResult) -> JSONResponse:
    headers = {"Idempotent-Replayed": "true"} if result.replayed else None
    media = "application/problem+json" if result.status >= 400 else "application/json"
    return JSONResponse(result.body, status_code=result.status, headers=headers, media_type=media)


def _require_key(key: str | None) -> str:
    if key is None:
        raise DomainError(400, "IDEMPOTENCY_KEY_MISSING", "Idempotency-Key header required")
    if not UUID4.fullmatch(key):
        raise DomainError(422, "VALIDATION_FAILED", "Idempotency-Key must be a UUIDv4")
    return key


def _store(request: Request) -> EventStore:
    store: EventStore = request.app.state.store
    return store


# --- reads ------------------------------------------------------------------------------


@router.get("/state", response_model=StateSnapshot, responses=PROBLEM_RESPONSES)
def get_state(
    request: Request,
    at_sequence: Annotated[int | None, Query(ge=1)] = None,
    session_id: str | None = None,
) -> Any:
    store = _store(request)
    if at_sequence is None:
        if session_id is not None and session_id != store.active_session():
            raise DomainError(
                410,
                "SNAPSHOT_REQUIRED",
                "Session is not current",
                current={"session_id": store.active_session()},
            )
        return store.state()
    if session_id is None:
        raise DomainError(422, "VALIDATION_FAILED", "Replay requires session_id")
    if not store.has_session(session_id):
        raise DomainError(404, "NOT_FOUND", "Unknown session")
    try:
        return store.state_at(session_id, at_sequence)
    except KeyError:
        raise DomainError(404, "NOT_FOUND", "Sequence not in this session") from None


@router.get("/events", response_model=list[EventEnvelope], responses=PROBLEM_RESPONSES)
def get_events(
    request: Request,
    session_id: str,
    after_sequence: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 500,
) -> Any:
    store = _store(request)
    active = store.active_session() or ""
    head = store.head_sequence(active)
    if session_id != active or after_sequence > head:
        raise DomainError(
            410,
            "SNAPSHOT_REQUIRED",
            "Snapshot required",
            f"Session {session_id} after {after_sequence} is not in the current history.",
            {"session_id": active, "head_sequence": head},
        )
    return [
        e.model_dump(mode="json", by_alias=True)
        for e in store.events(active, after_sequence, limit)
    ]


# --- routing (CC-07) --------------------------------------------------------------------


def _routing(request: Request) -> RouteService:
    service: RouteService | None = getattr(request.app.state, "routing", None)
    if service is None:
        service = RouteService()
        request.app.state.routing = service
    return service


@router.get("/routing/route", response_model=Route, responses=PROBLEM_RESPONSES)
def get_route(
    request: Request,
    from_lon: Annotated[float, Query(ge=-180, le=180)],
    from_lat: Annotated[float, Query(ge=-90, le=90)],
    to_lon: Annotated[float, Query(ge=-180, le=180)],
    to_lat: Annotated[float, Query(ge=-90, le=90)],
) -> Any:
    """Fastest open road route under the current session's flood closures."""
    route = _routing(request).route(_store(request).state(), (from_lon, from_lat), (to_lon, to_lat))
    return route.model_dump(mode="json", by_alias=True)


@router.get("/routing/candidates", response_model=RouteCandidates, responses=PROBLEM_RESPONSES)
def get_route_candidates(request: Request, incident_id: str) -> Any:
    """Fastest road route from every unit to an incident (informational; not an allocation)."""
    try:
        result = _routing(request).candidates(_store(request).state(), incident_id)
    except KeyError:
        raise DomainError(
            404, "NOT_FOUND", "Unknown incident", f"{incident_id} is not in this session"
        ) from None
    return result.model_dump(mode="json", by_alias=True)


# --- commands ---------------------------------------------------------------------------


def _unit_response(events: list[EnvelopeBase]) -> tuple[int, dict[str, Any]]:
    event = events[0]
    payload = event.payload
    assert isinstance(payload, UnitStatusChangedPayload)
    body = UnitStatusAccepted(
        unit_id=payload.unit.unit_id,
        status=payload.unit.status,
        sequence=event.sequence,
        invalidated_assignment_ids=payload.invalidates_assignment_ids,
    )
    return 200, body.model_dump(mode="json")


@router.post(
    "/units/{unit_id}/status", response_model=UnitStatusAccepted, responses=PROBLEM_RESPONSES
)
def post_unit_status(
    request: Request,
    unit_id: str,
    command: UnitStatusCommand,
    idempotency_key: IdempotencyKey = None,
) -> JSONResponse:
    key = _require_key(idempotency_key)
    result = _store(request).execute(
        method="POST",
        path=f"/units/{unit_id}/status",
        key=key,
        body=command.model_dump(mode="json", by_alias=True),
        expected_session_id=command.expected_session_id,
        decide=lambda state: Decision([unit_status(state, unit_id, command)], _unit_response),
        actor=OPERATOR,
    )
    return _result_response(result)


def _flood_payload(event: EnvelopeBase) -> FloodZoneUpdatedPayload:
    payload = event.payload
    assert isinstance(payload, FloodZoneUpdatedPayload)
    return payload


def _flood_response(events: list[EnvelopeBase]) -> tuple[int, dict[str, Any]]:
    event = events[0]
    body = FloodAccepted(
        flood_id=event.aggregate_id,
        version=_flood_payload(event).flood.version,
        sequence=event.sequence,
    )
    return 201, body.model_dump(mode="json")


@router.post(
    "/flood-events", status_code=201, response_model=FloodAccepted, responses=PROBLEM_RESPONSES
)
def post_flood_event(
    request: Request, command: FloodEventCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    key = _require_key(idempotency_key)
    result = _store(request).execute(
        method="POST",
        path="/flood-events",
        key=key,
        body=command.model_dump(mode="json", by_alias=True),
        expected_session_id=command.expected_session_id,
        decide=lambda state: Decision([flood_update(state, command)], _flood_response),
        actor=OPERATOR,
    )
    return _result_response(result)


@router.post(
    "/demo/reset",
    response_model=DemoResetResult,
    responses={403: {"model": Problem}, **PROBLEM_RESPONSES},
)
def post_demo_reset(
    request: Request, command: DemoResetCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    key = _require_key(idempotency_key)
    if request.app.state.settings.mode != "simulation":  # pragma: no cover - only mode today
        raise DomainError(403, "SIMULATION_ONLY", "Simulation-only endpoint")
    result = _store(request).reset(
        key=key,
        body=command.model_dump(mode="json", by_alias=True),
        expected_session_id=command.expected_session_id,
        fixture=command.fixture,
        seed=command.seed,
    )
    return _result_response(result)


# --- error handling ---------------------------------------------------------------------


def _pointer(loc: tuple[Any, ...]) -> str:
    parts = [str(p) for p in loc if p not in ("body", "query", "path", "header")]
    return "/" + "/".join(parts)


def install(app: FastAPI) -> None:
    app.include_router(router)

    @app.exception_handler(DomainError)
    async def _domain(_: Request, exc: DomainError) -> JSONResponse:
        return problem_response(exc)

    @app.exception_handler(DatabaseBusyError)
    async def _busy(_: Request, __: DatabaseBusyError) -> JSONResponse:
        error = DomainError(
            503, "DATABASE_BUSY", "Database busy", "Retry the same request with the same key."
        )
        return problem_response(error, {"Retry-After": "1"})

    @app.exception_handler(RequestValidationError)
    async def _invalid(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for err in exc.errors():
            kind = str(err.get("type", ""))
            message = str(err.get("msg", ""))
            if kind.isupper():
                message = f"{kind}: {message}"
            errors.append({"pointer": _pointer(tuple(err.get("loc", ()))), "message": message})
        body = problem(DomainError(422, "VALIDATION_FAILED", "Request failed validation"))
        body["errors"] = errors
        return JSONResponse(body, status_code=422, media_type="application/problem+json")
