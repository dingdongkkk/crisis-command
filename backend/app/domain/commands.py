"""Pure command decisions: current state + command -> events to append, or a DomainError.

The storage layer supplies envelope metadata (sequence, IDs, clocks); these functions
decide only *what* happened, so they are trivially testable and replay-safe.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.contracts.commands import FloodEventCommand, UnitStatusCommand
from app.contracts.common import SCHEMA_VERSION
from app.contracts.entities import FloodZone
from app.contracts.enums import UnitStatus
from app.contracts.events import (
    FloodZoneUpdatedPayload,
    SessionStartedPayload,
    UnitStatusChangedPayload,
)
from app.contracts.state import StateSnapshot

FIXTURES = Path(__file__).resolve().parents[3] / "evals" / "fixtures"

# Statuses that end a unit's current task (0003 H2): the assignment is invalidated.
UNAVAILABLE = frozenset({UnitStatus.BROKEN_DOWN, UnitStatus.OUT_OF_SERVICE, UnitStatus.OFF_DUTY})
# Statuses that release the task normally (operator clears the unit).
RELEASING = frozenset({UnitStatus.AVAILABLE, UnitStatus.RETURNING})
# Statuses meaningful only while the unit has a task.
TASK_BOUND = frozenset(
    {UnitStatus.EN_ROUTE, UnitStatus.ON_SCENE, UnitStatus.TRANSPORTING, UnitStatus.AT_FACILITY}
)


@dataclass
class DomainError(Exception):
    """A business rejection, rendered as RFC 9457 problem details by the API."""

    status: int
    code: str
    title: str
    detail: str | None = None
    current: dict[str, Any] | None = None


@dataclass(frozen=True)
class NewEvent:
    """An event decided by the domain; storage adds envelope metadata when appending."""

    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: Any
    sim_time_s: int
    extra: dict[str, Any] = field(default_factory=dict)


def load_fixture(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((FIXTURES / f"{name}.json").read_text())
    data.pop("_comment", None)
    return data


def session_started(session_id: str, fixture: str, seed: int) -> NewEvent:
    world = load_fixture(fixture)
    initial = StateSnapshot.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "as_of_sequence": 0,
            "planning_sequence": 0,
            "sim_time_s": 0,
            "policy": world["policy"],
            "incidents": [],
            "reports": [],
            "triage_facts": [],
            "units": world["units"],
            "facilities": world["facilities"],
            "flood": [],
            "reserve_zones": world["reserve_zones"],
            "active_overrides": [],
            "approved_plan": None,
            "current_proposal": None,
            "outbox": [],
        }
    )
    payload = SessionStartedPayload(fixture=fixture, seed=seed, initial_state=initial)
    return NewEvent("SessionStarted", "session", session_id, payload, 0)


def unit_status(state: StateSnapshot, unit_id: str, command: UnitStatusCommand) -> NewEvent:
    unit = next((u for u in state.units if u.unit_id == unit_id), None)
    if unit is None:
        raise DomainError(404, "NOT_FOUND", "Unknown unit", f"{unit_id} is not in this session")
    target = command.to_status
    if target == unit.status:
        raise DomainError(
            409, "INVALID_TRANSITION", "No status change", f"{unit_id} is already {target.value}"
        )
    if target in TASK_BOUND and unit.current_task is None:
        raise DomainError(
            409,
            "INVALID_TRANSITION",
            "Unit has no task",
            f"{unit_id} cannot become {target.value} without an approved, delivered task",
        )
    if command.sim_time_s < state.sim_time_s:
        raise DomainError(409, "INVALID_TRANSITION", "Simulation time went backwards")
    invalidated: list[str] = []
    updated = unit.model_copy(deep=True)
    updated.status = target
    if command.position is not None:
        updated.position = command.position
        updated.position_sim_time_s = command.sim_time_s
    if target in UNAVAILABLE:
        updated.desired_revision = (unit.desired_revision or 0) + 1
    if (target in UNAVAILABLE or target in RELEASING) and unit.current_task is not None:
        invalidated.append(unit.current_task.assignment_id)
        updated.current_task = None
        # A changed desired target fences any pending dispatch command for the old task.
        updated.desired_revision = (unit.desired_revision or 0) + 1
    payload = UnitStatusChangedPayload(unit=updated, invalidates_assignment_ids=invalidated)
    return NewEvent("UnitStatusChanged", "unit", unit_id, payload, command.sim_time_s)


def flood_update(state: StateSnapshot, command: FloodEventCommand) -> NewEvent:
    current = next((f for f in state.flood if f.flood_id == command.flood_id), None)
    expected = 1 if current is None else current.version + 1
    if command.version != expected:
        raise DomainError(
            409,
            "INVALID_TRANSITION",
            "Flood version out of order",
            f"{command.flood_id} expects version {expected}",
            {"flood_id": command.flood_id, "expected_version": expected},
        )
    flood = FloodZone(
        flood_id=command.flood_id,
        version=command.version,
        effective_sim_time_s=command.effective_sim_time_s,
        closes_roads=command.closes_roads,
        geometry=command.geometry,
        source="operator_entered",
    )
    return NewEvent(
        "FloodZoneUpdated",
        "flood",
        command.flood_id,
        FloodZoneUpdatedPayload(flood=flood),
        max(command.effective_sim_time_s, state.sim_time_s),
    )
