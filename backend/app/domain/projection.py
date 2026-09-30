"""Deterministic world projection: ``state = fold(apply, events)`` (decision 0005).

Pure functions only: no I/O, clocks or randomness. Replay never calls the solver,
router, models or the dispatch sender; it reads their recorded results from events.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from typing import Any

from app.contracts.enums import DispatchState, PlanState
from app.contracts.events import (
    EVENT_CATALOG,
    EnvelopeBase,
    FacilityCapacityUpdatedPayload,
    FloodZoneUpdatedPayload,
    IncidentCategoryChangedPayload,
    IncidentPayload,
    IncidentResolvedPayload,
    OverrideEndedPayload,
    OverridePayload,
    PlanApprovedPayload,
    PlanningTickCommittedPayload,
    PlanProposedPayload,
    PlanRevalidatedPayload,
    PlanSupersededPayload,
    ReportLinkedToIncidentPayload,
    ReportReceivedPayload,
    SessionStartedPayload,
    SimulatedDispatchEndedPayload,
    SimulatedDispatchQueuedPayload,
    SimulatedDispatchSentPayload,
    TriageFactConfirmedPayload,
    TriageFactsExtractedPayload,
    UnitStatusChangedPayload,
)
from app.contracts.state import StateSnapshot


class ProjectionError(ValueError):
    """An event cannot be applied to the current state (log corruption or ordering bug)."""


Handler = Callable[[dict[str, Any], Any], None]


def _upsert(items: list[dict[str, Any]], key: str, item: dict[str, Any]) -> None:
    for i, existing in enumerate(items):
        if existing[key] == item[key]:
            items[i] = item
            return
    items.append(item)


def _dump(model: Any) -> Any:
    return model.model_dump(mode="json", by_alias=True, exclude_none=False)


def _session_started(state: dict[str, Any], p: SessionStartedPayload) -> None:
    state.clear()
    state.update(_dump(p.initial_state))


def _report(state: dict[str, Any], p: ReportReceivedPayload) -> None:
    _upsert(state["reports"], "report_id", _dump(p.report))


def _triage(state: dict[str, Any], p: TriageFactsExtractedPayload) -> None:
    _upsert(state["triage_facts"], "incident_id", _dump(p.triage_facts))


def _fact_confirmed(state: dict[str, Any], p: TriageFactConfirmedPayload) -> None:
    for facts in state["triage_facts"]:
        if facts["incident_id"] == p.incident_id:
            _upsert(facts["facts"], "key", _dump(p.fact))
            return
    raise ProjectionError(f"no triage facts for {p.incident_id}")


def _incident(state: dict[str, Any], p: IncidentPayload | IncidentCategoryChangedPayload) -> None:
    _upsert(state["incidents"], "incident_id", _dump(p.incident))


def _report_linked(state: dict[str, Any], p: ReportLinkedToIncidentPayload) -> None:
    if p.resolution != "linked":
        return
    for report in state["reports"]:
        if report["report_id"] == p.report_id:
            report["linked_incident_id"] = p.incident_id
    for incident in state["incidents"]:
        if incident["incident_id"] == p.incident_id and p.report_id not in incident["report_ids"]:
            incident["report_ids"].append(p.report_id)


def _incident_resolved(state: dict[str, Any], p: IncidentResolvedPayload) -> None:
    for incident in state["incidents"]:
        if incident["incident_id"] == p.incident_id:
            incident["status"] = "resolved"
            return
    raise ProjectionError(f"unknown incident {p.incident_id}")


def _unit(state: dict[str, Any], p: UnitStatusChangedPayload) -> None:
    _replace_unit(state, _dump(p.unit))


def _replace_unit(state: dict[str, Any], unit: dict[str, Any]) -> None:
    for i, existing in enumerate(state["units"]):
        if existing["unit_id"] == unit["unit_id"]:
            state["units"][i] = unit
            return
    raise ProjectionError(f"unknown unit {unit['unit_id']}")


def _tick(state: dict[str, Any], p: PlanningTickCommittedPayload) -> None:
    by_id = {u["unit_id"]: u for u in state["units"]}
    for tick in p.units:
        unit = by_id.get(tick.unit_id)
        if unit is None:
            raise ProjectionError(f"unknown unit {tick.unit_id}")
        unit["position"] = _dump(tick.position)
        unit["position_sim_time_s"] = p.tick_sim_time_s


def _flood(state: dict[str, Any], p: FloodZoneUpdatedPayload) -> None:
    _upsert(state["flood"], "flood_id", _dump(p.flood))


def _capacity(state: dict[str, Any], p: FacilityCapacityUpdatedPayload) -> None:
    for facility in state["facilities"]:
        if facility["facility_id"] == p.facility_id:
            if p.ed_beds_available is not None:
                facility["ed_beds_available"] = p.ed_beds_available
            if p.occupied_persons is not None:
                facility["occupied_persons"] = p.occupied_persons
            return
    raise ProjectionError(f"unknown facility {p.facility_id}")


def _override_accepted(state: dict[str, Any], p: OverridePayload) -> None:
    _upsert(state["active_overrides"], "override_id", _dump(p.override))


def _override_ended(state: dict[str, Any], p: OverrideEndedPayload) -> None:
    state["active_overrides"] = [
        o for o in state["active_overrides"] if o["override_id"] != p.override_id
    ]


def _plan_proposed(state: dict[str, Any], p: PlanProposedPayload) -> None:
    # Only one current proposal exists; publishing a new one supersedes the old (0005).
    state["current_proposal"] = _dump(p.plan)


def _plan_superseded(state: dict[str, Any], p: PlanSupersededPayload) -> None:
    proposal = state["current_proposal"]
    if proposal is not None and proposal["plan_id"] == p.plan_id:
        state["current_proposal"] = None


def _plan_revalidated(state: dict[str, Any], p: PlanRevalidatedPayload) -> None:
    proposal = state["current_proposal"]
    if (
        proposal is not None
        and proposal["based_on_planning_sequence"] < p.checked_planning_sequence
    ):
        state["current_proposal"] = None


def _plan_approved(state: dict[str, Any], p: PlanApprovedPayload) -> None:
    proposal = state["current_proposal"]
    if proposal is None or proposal["plan_id"] != p.plan_id or proposal["version"] != p.version:
        raise ProjectionError(f"approval of {p.plan_id} does not match the current proposal")
    proposal["state"] = (
        PlanState.DISPATCHING.value if p.outbox_keys else PlanState.DISPATCHED_SIMULATED.value
    )
    state["approved_plan"] = proposal
    state["current_proposal"] = None
    revisions = {d.unit_id: d.desired_revision for d in p.desired_assignments}
    for unit in state["units"]:
        if unit["unit_id"] in revisions:
            unit["desired_revision"] = revisions[unit["unit_id"]]


def _find_command(state: dict[str, Any], outbox_key: str) -> dict[str, Any]:
    for command in state["outbox"]:
        if command["outbox_key"] == outbox_key:
            found: dict[str, Any] = command
            return found
    raise ProjectionError(f"unknown outbox command {outbox_key}")


def _refresh_dispatch_state(state: dict[str, Any]) -> None:
    plan = state["approved_plan"]
    if plan is None:
        return
    commands = [c for c in state["outbox"] if c["plan_id"] == plan["plan_id"]]
    states = {c["state"] for c in commands}
    if DispatchState.PENDING.value in states:
        plan["state"] = PlanState.DISPATCHING.value
    elif states - {DispatchState.SENT.value}:
        plan["state"] = PlanState.DISPATCH_PARTIAL_FAILED.value
    else:
        plan["state"] = PlanState.DISPATCHED_SIMULATED.value


def _dispatch_queued(state: dict[str, Any], p: SimulatedDispatchQueuedPayload) -> None:
    _upsert(state["outbox"], "outbox_key", _dump(p.command))
    _refresh_dispatch_state(state)


def _dispatch_sent(state: dict[str, Any], p: SimulatedDispatchSentPayload) -> None:
    _find_command(state, p.outbox_key)["state"] = DispatchState.SENT.value
    if p.unit_after is not None:
        _replace_unit(state, _dump(p.unit_after))
    _refresh_dispatch_state(state)


def _dispatch_ended(terminal: DispatchState) -> Handler:
    def handler(state: dict[str, Any], p: SimulatedDispatchEndedPayload) -> None:
        _find_command(state, p.outbox_key)["state"] = terminal.value
        _refresh_dispatch_state(state)

    return handler


def _no_state_change(state: dict[str, Any], payload: Any) -> None:
    """Audit-only events (escalations, rejections, access logs, raw telemetry)."""


HANDLERS: dict[str, Handler] = {
    "SessionStarted": _session_started,
    "ReportReceived": _report,
    "TriageFactsExtracted": _triage,
    "TriageFactConfirmed": _fact_confirmed,
    "IncidentCreated": _incident,
    "IncidentAssessed": _incident,
    "IncidentCategoryChanged": _incident,
    "ReportLinkedToIncident": _report_linked,
    "IncidentResolved": _incident_resolved,
    "UnitStatusChanged": _unit,
    "PlanningTickCommitted": _tick,
    "FloodZoneUpdated": _flood,
    # Road closures join routing state in CC-07; they carry no snapshot field in v1.0.
    "RoadClosureUpdated": _no_state_change,
    "FacilityCapacityUpdated": _capacity,
    "OverrideAccepted": _override_accepted,
    "OverrideInvalidated": _override_ended,
    "OverrideRevoked": _override_ended,
    "PlanApproved": _plan_approved,
    "SimulatedDispatchSent": _dispatch_sent,
    "UnitPositionObserved": _no_state_change,
    "EscalatedToHuman": _no_state_change,
    "DuplicateCandidateFlagged": _no_state_change,
    "PlanProposed": _plan_proposed,
    "PlanSuperseded": _plan_superseded,
    "PlanRevalidated": _plan_revalidated,
    "PlanFailed": _no_state_change,
    "ApprovalRejected": _no_state_change,
    "OverrideRejected": _no_state_change,
    "SimulatedDispatchQueued": _dispatch_queued,
    "SimulatedDispatchCancelled": _dispatch_ended(DispatchState.CANCELLED),
    "SimulatedDispatchFailed": _dispatch_ended(DispatchState.FAILED),
    "MedicalProfileAccessGranted": _no_state_change,
    "MedicalProfileAccessDenied": _no_state_change,
    "HospitalPreAlertSimulated": _no_state_change,
    "ModelAdapterDegraded": _no_state_change,
}


def apply(state: StateSnapshot | None, event: EnvelopeBase) -> StateSnapshot:
    """Apply one event. ``state`` is ``None`` only before a session's ``SessionStarted``."""
    event_type: str = event.event_type
    if state is None:
        if event_type != "SessionStarted" or event.sequence != 1:
            raise ProjectionError("a session log must begin with SessionStarted at sequence 1")
        working: dict[str, Any] = {}
    else:
        if event.session_id != state.session_id:
            raise ProjectionError("event belongs to a different session")
        if event.sequence != state.as_of_sequence + 1:
            raise ProjectionError(
                f"sequence gap: have {state.as_of_sequence}, got {event.sequence}"
            )
        working = state.model_dump(mode="json", by_alias=True)
    HANDLERS[event_type](working, event.payload)
    working["session_id"] = event.session_id
    working["as_of_sequence"] = event.sequence
    working["sim_time_s"] = max(working.get("sim_time_s", 0), event.sim_time_s)
    if event.affects_planning:
        working["planning_sequence"] = event.sequence
    working.pop("historical_plans", None)
    return StateSnapshot.model_validate(working)


def fold(events: Iterable[EnvelopeBase], state: StateSnapshot | None = None) -> StateSnapshot:
    for event in events:
        state = apply(state, event)
    if state is None:
        raise ProjectionError("no events to fold")
    return state


def state_hash(state: StateSnapshot) -> str:
    """Operational-state hash for replay equivalence (excludes wall-clock-only data)."""
    body = state.model_dump(mode="json", by_alias=True, exclude={"historical_plans"})
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


if set(HANDLERS) != set(EVENT_CATALOG):  # pragma: no cover - import-time guard
    raise RuntimeError("projection handlers and event catalog drifted")
