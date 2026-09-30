"""Versioned policy, dispatch outbox commands and the state snapshot (0003, 0005)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from .common import Contract, Id, SchemaVersion, Seconds
from .entities import (
    Facility,
    FloodZone,
    Incident,
    Override,
    Report,
    ReserveZone,
    TriageFacts,
    Unit,
)
from .enums import DispatchAction, DispatchState, ObjectiveTier, Severity
from .plan import OBJECTIVE_TIERS, Plan

PositiveInt = Annotated[int, Field(ge=1)]


class PolicyLimits(Contract):
    units: PositiveInt
    need_records: PositiveInt
    demand_quanta: PositiveInt
    reserve_pairs: PositiveInt


class PolicyCosts(Contract):
    travel_cap_s: Seconds
    waiting_cap_s: Seconds
    reassignment: Annotated[int, Field(ge=0)]
    reserve_shortfall: Annotated[int, Field(ge=0)]
    als_on_bls: Annotated[int, Field(ge=0)]


class Policy(Contract):
    """Demonstration policy; values are not clinical or operational standards."""

    policy_version: Annotated[str, Field(pattern=r"^demo-\d{4}\.\d+$")]
    dangerous_values: dict[str, Literal["yes", "no"]]
    objective_tiers: list[ObjectiveTier]
    severity_weights: dict[Severity, PositiveInt]
    limits: PolicyLimits
    costs: PolicyCosts
    planning_tick_s: PositiveInt
    max_debounce_ms: Annotated[int, Field(ge=0)]
    solver_budget_ms: PositiveInt
    near_arrival_lock_s: Seconds

    @model_validator(mode="after")
    def _tiers_and_weights(self) -> Policy:
        if tuple(self.objective_tiers) != OBJECTIVE_TIERS:
            raise PydanticCustomError("TIER_ORDER", "objective tiers must follow 0003 order")
        if set(self.severity_weights) != set(Severity):
            raise PydanticCustomError("SEVERITY_WEIGHTS", "every severity needs a weight")
        return self


class DispatchCommand(Contract):
    """Simulated outbox command. ``simulated`` is always true; no real transport exists."""

    session_id: Id
    outbox_key: Id
    plan_id: Id
    action: DispatchAction
    unit_id: Id | None = None
    assignment_id: Id
    incident_id: Id | None = None
    desired_revision: Annotated[int, Field(ge=0)]
    state: DispatchState
    simulated: Literal[True]

    @model_validator(mode="after")
    def _session_qualified_key(self) -> DispatchCommand:
        prefix = f"{self.session_id}:{self.plan_id}:{self.action.value}:"
        if not self.outbox_key.startswith(prefix):
            raise PydanticCustomError(
                "OUTBOX_KEY_FORMAT",
                "outbox_key is session_id:plan_id:action:assignment_or_alert_id",
            )
        return self


class StateSnapshot(Contract):
    """``GET /state`` body; also the checkpoint embedded in ``SessionStarted``."""

    schema_version: SchemaVersion
    session_id: Id
    as_of_sequence: Annotated[int, Field(ge=0)]
    planning_sequence: Annotated[int, Field(ge=0)]
    sim_time_s: Seconds
    policy: Policy
    incidents: list[Incident]
    reports: list[Report]
    triage_facts: list[TriageFacts]
    units: list[Unit]
    facilities: list[Facility]
    flood: list[FloodZone]
    reserve_zones: list[ReserveZone]
    active_overrides: list[Override]
    approved_plan: Plan | None
    current_proposal: Plan | None
    outbox: list[DispatchCommand]
    historical_plans: list[Plan] | None = None

    @model_validator(mode="after")
    def _sequences(self) -> StateSnapshot:
        if self.planning_sequence > self.as_of_sequence:
            raise PydanticCustomError("SEQUENCE_ORDER", "planning_sequence <= as_of_sequence")
        return self
