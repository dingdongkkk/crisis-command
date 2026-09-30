"""Plan envelope, assignments, unmet needs, flags and diff (0003, 0005)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from .common import (
    Code,
    Contract,
    Id,
    Persons,
    ReasonFact,
    SchemaVersion,
    Seconds,
    UtcTimestamp,
    Version,
)
from .entities import Route
from .enums import (
    AssignmentRole,
    CoverageStatus,
    FlagSeverity,
    LockReason,
    NeedBasis,
    NeedType,
    ObjectiveTier,
    PlanState,
    Severity,
    SolverStatus,
    UnitType,
)


class Assignment(Contract):
    assignment_id: Id
    unit_id: Id
    incident_id: Id
    need_id: Id | None = None
    role: AssignmentRole
    satisfies_need: bool
    bridges_need_id: Id | None = None
    eta_s: Seconds
    locked: LockReason | None
    persons: Persons | None = None
    destination_facility_id: Id | None = None
    route: Route
    onward_route: Route | None = None
    reasons: list[ReasonFact]

    @model_validator(mode="after")
    def _role_rules(self) -> Assignment:
        if self.role is AssignmentRole.BRIDGE:
            # 0003: a BLS bridge never satisfies the ALS need it bridges.
            if self.satisfies_need:
                raise PydanticCustomError(
                    "BRIDGE_CANNOT_SATISFY", "a bridge assignment never satisfies the need"
                )
            if self.bridges_need_id is None or self.need_id is not None:
                raise PydanticCustomError(
                    "BRIDGE_SHAPE", "bridges name bridges_need_id and no need_id"
                )
        else:
            if self.need_id is None or self.bridges_need_id is not None or not self.satisfies_need:
                raise PydanticCustomError(
                    "PRIMARY_SHAPE", "primary assignments satisfy exactly one need_id"
                )
        return self


class FacilityAllocation(Contract):
    allocation_id: Id
    facility_id: Id
    incident_id: Id
    need_id: Id
    persons: Annotated[int, Field(ge=1)]
    free_after_persons: Persons
    route: Route | None = None


class CostOfTaking(Contract):
    metric: Literal[
        "unmet_need",
        "reserve_uncovered",
        "already_assigned_same_incident",
        "weighted_eta_s",
    ]
    need_id: Id | None = None
    zone_id: Id | None = None
    delta: int | None = None


class BridgeCandidate(Contract):
    unit_id: Id
    eta_s: Seconds
    cost_of_taking: list[CostOfTaking]


class UnmetNeed(Contract):
    need_id: Id
    incident_id: Id
    type: NeedType
    quantity_unmet: Annotated[int, Field(ge=1)]
    severity: Severity
    basis: NeedBasis
    waiting_s: Seconds
    reasons: list[ReasonFact]
    bridge_candidates: Annotated[list[BridgeCandidate], Field(max_length=3)] = Field(
        default_factory=list
    )


class PolicyFlag(Contract):
    flag_id: Id
    code: Code
    severity: FlagSeverity
    requires_ack: bool
    message: str
    incident_id: Id | None = None
    need_id: Id | None = None
    zone_id: Id | None = None
    resource_type: UnitType | None = None
    since_sim_time_s: Seconds | None = None
    override_id: Id | None = None

    @model_validator(mode="before")
    @classmethod
    def _ack_explicit(cls, data: Any) -> Any:
        if isinstance(data, dict) and "requires_ack" not in data:
            raise PydanticCustomError(
                "ACK_FIELD_REQUIRED", "every flag states requires_ack explicitly"
            )
        return data


class Coverage(Contract):
    zone_id: Id
    resource_type: UnitType
    status: CoverageStatus
    available_unit_ids: list[Id]


class DiffEndpoint(Contract):
    state: Literal["available", "assigned", "held"] | None = None
    zone_id: Id | None = None
    incident_id: Id | None = None
    need_id: Id | None = None
    eta_s: Seconds | None = None


class DiffRow(Contract):
    unit_id: Id
    from_: DiffEndpoint = Field(alias="from")
    to: DiffEndpoint | None = None
    reason: ReasonFact | None = None


class DiffTotals(Contract):
    weighted_eta_delta_s: int
    units_moved: Persons
    units_added: Persons
    units_released: Persons
    needs_unmet: Persons
    zones_uncovered: Persons


class PlanDiff(Contract):
    against_plan_id: Id | None
    changed: list[DiffRow]
    added: list[DiffRow]
    released: list[DiffRow]
    unchanged_count: Persons
    newly_unmet: list[Id]
    totals: DiffTotals


class SoftConsequence(Contract):
    metric: Literal["weighted_eta_s", "reserve_uncovered", "unmet_need"]
    delta: int | None = None
    zone_id: Id | None = None
    need_id: Id | None = None
    override_id: Id | None = None


OBJECTIVE_TIERS = tuple(ObjectiveTier)


class SolverResult(Contract):
    engine: Literal["ortools_cp_sat", "greedy_fallback"]
    status: SolverStatus
    wall_time_ms: Annotated[int, Field(ge=0)]
    seed: int
    workers: Annotated[int, Field(ge=1)]
    objective_vector: Annotated[
        list[Annotated[int, Field(ge=0)]], Field(min_length=6, max_length=6)
    ]
    completed_tiers: list[ObjectiveTier]
    lexicographic_complete: bool
    tie_break_complete: bool

    @model_validator(mode="after")
    def _tiers_are_a_prefix(self) -> SolverResult:
        # 0003: lower tiers are never optimised after an unproven higher tier.
        if list(self.completed_tiers) != list(OBJECTIVE_TIERS[: len(self.completed_tiers)]):
            raise PydanticCustomError(
                "TIER_ORDER", "completed_tiers must be a prefix of the tier order"
            )
        if self.lexicographic_complete != (len(self.completed_tiers) == len(OBJECTIVE_TIERS)):
            raise PydanticCustomError(
                "TIER_COMPLETENESS", "lexicographic_complete iff every tier is proven"
            )
        return self


class Plan(Contract):
    schema_version: SchemaVersion
    session_id: Id
    plan_id: Id
    version: Version
    state: PlanState
    based_on_planning_sequence: Annotated[int, Field(ge=1)]
    created_sim_time_s: Seconds
    created_at: UtcTimestamp
    policy_version: str
    supersedes_approved_plan_id: Id | None = None
    solver: SolverResult
    assignments: list[Assignment]
    facility_allocations: list[FacilityAllocation]
    unmet_needs: list[UnmetNeed]
    flags: list[PolicyFlag]
    coverage: list[Coverage]
    diff: PlanDiff
    soft_consequences: list[SoftConsequence]

    @model_validator(mode="after")
    def _self_contained_invariants(self) -> Plan:
        units = [a.unit_id for a in self.assignments]
        if len(units) != len(set(units)):
            raise PydanticCustomError("DUPLICATE_UNIT", "a unit has at most one task (H4)")
        flag_ids = [f.flag_id for f in self.flags]
        if len(flag_ids) != len(set(flag_ids)):
            raise PydanticCustomError("DUPLICATE_FLAG_ID", "flag IDs are unique per plan")
        for assignment in self.assignments:
            for route in (assignment.route, assignment.onward_route):
                if route is not None and route.route_status != "ok":
                    raise PydanticCustomError(
                        "ROUTE_UNAVAILABLE", "assignments require an ok route (H5)"
                    )
        return self
