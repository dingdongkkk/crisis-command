"""API command bodies, responses and WebSocket messages (0001, 0004, 0005, 0008).

Every mutating body carries ``expected_session_id`` and is sent with an
``Idempotency-Key`` header. Commands reject unknown fields.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from .common import Code, Contract, Id, Point, Polygon, SchemaVersion, Seconds, Version
from .entities import Route
from .enums import FactValue, OverrideKind, UnitStatus, UnitType
from .events import EventEnvelope

ReasonText = Annotated[str, Field(min_length=1, max_length=280)]


class SessionBound(Contract):
    expected_session_id: Id


class ReportCommand(SessionBound):
    channel: Literal["text_sim", "structured_sim"]
    text: Annotated[str, Field(min_length=1, max_length=2000)]
    location: Point
    location_source: Literal["caller_stated", "operator_entered", "fixture"]
    sim_time_s: Seconds


class AnswerCommand(SessionBound):
    fact_key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    answer: FactValue


class FactConfirmCommand(SessionBound):
    value: FactValue | None = None
    count: Annotated[int, Field(ge=0)] | None = None
    reason_text: ReasonText


class DuplicateResolveCommand(SessionBound):
    resolution: Literal["linked", "kept_separate"]
    reason_text: ReasonText


class MedicalProfileAccessCommand(SessionBound):
    profile_ref: Id
    operator_reason: ReasonText


class UnitStatusCommand(SessionBound):
    to_status: UnitStatus
    position: Point | None = None
    sim_time_s: Seconds


class FloodEventCommand(SessionBound):
    flood_id: Id
    version: Version
    closes_roads: bool
    effective_sim_time_s: Seconds
    geometry: Polygon


class RecomputeCommand(SessionBound):
    reason: Literal["operator_requested"]


class ApproveCommand(SessionBound):
    expected_plan_version: Version
    expected_planning_sequence: Annotated[int, Field(ge=1)]
    acknowledged_flag_ids: list[Id]
    note: Annotated[str, Field(max_length=280)] | None = None


# Fields each override kind requires (0004).
_OVERRIDE_FIELDS: dict[OverrideKind, frozenset[str]] = {
    OverrideKind.PIN: frozenset({"unit_id", "need_id"}),
    OverrideKind.FORBID: frozenset({"unit_id", "incident_id"}),
    OverrideKind.HOLD_UNIT: frozenset({"unit_id"}),
    OverrideKind.APPROVE_BLS_BRIDGE: frozenset({"unit_id", "bridges_need_id"}),
    OverrideKind.DOWNGRADE_NEED: frozenset({"need_id"}),
    OverrideKind.REVOKE: frozenset({"revokes_override_id"}),
}
_OPTIONAL_OVERRIDE_FIELDS = frozenset({"zone_id", "replaces_override_id"})
_TARGET_FIELDS = frozenset(
    {"unit_id", "need_id", "incident_id", "bridges_need_id", "revokes_override_id", "zone_id"}
)


class OverrideCommand(SessionBound):
    kind: OverrideKind
    unit_id: Id | None = None
    need_id: Id | None = None
    incident_id: Id | None = None
    zone_id: Id | None = None
    bridges_need_id: Id | None = None
    revokes_override_id: Id | None = None
    replaces_override_id: Id | None = None
    expected_plan_id: Id
    expected_planning_sequence: Annotated[int, Field(ge=1)]
    reason_text: ReasonText

    @model_validator(mode="after")
    def _fields_for_kind(self) -> OverrideCommand:
        required = _OVERRIDE_FIELDS[self.kind]
        present = {f for f in _TARGET_FIELDS if getattr(self, f) is not None}
        allowed = required | (
            _OPTIONAL_OVERRIDE_FIELDS if self.kind is OverrideKind.HOLD_UNIT else set()
        )
        if not required <= present or present - allowed:
            raise PydanticCustomError(
                "OVERRIDE_FIELDS",
                "override {kind} requires exactly {required}",
                {"kind": self.kind.value, "required": sorted(required)},
            )
        return self


class DemoResetCommand(SessionBound):
    fixture: Literal["demo-bengaluru-v1"]
    seed: int


class DemoAdvanceCommand(SessionBound):
    to_step: Literal["T+0", "T+2", "T+5", "T+10"]


# --- Responses --------------------------------------------------------------------------


class HealthResponse(Contract):
    status: Literal["ok"]
    mode: Literal["simulation"]
    schema_version: SchemaVersion
    routing_provider: Literal["fixture", "ors_directions"]
    llm_provider: Literal["template", "gemini"]
    degraded: list[Code]


class ReportAccepted(Contract):
    report_id: Id
    incident_id: Id | None
    sequence: Annotated[int, Field(ge=1)]
    escalated: bool


class UnitStatusAccepted(Contract):
    unit_id: Id
    status: UnitStatus
    sequence: Annotated[int, Field(ge=1)]
    invalidated_assignment_ids: list[Id]


class FloodAccepted(Contract):
    flood_id: Id
    version: Version
    sequence: Annotated[int, Field(ge=1)]


class RecomputeAccepted(Contract):
    status: Literal["computing"]
    planning_sequence: Annotated[int, Field(ge=1)]


class ApprovalAccepted(Contract):
    plan_id: Id
    state: Literal["approved", "dispatched_simulated"]
    sequence: Annotated[int, Field(ge=1)]
    outbox_keys: list[Id]


class OverrideRecorded(Contract):
    override_id: Id
    status: Literal["active"]
    sequence: Annotated[int, Field(ge=1)]
    recompute: Literal["computing"]


class DemoResetResult(Contract):
    session_id: Id
    head_sequence: Annotated[int, Field(ge=1)]


class DemoAdvanceResult(Contract):
    sim_time_s: Seconds
    head_sequence: Annotated[int, Field(ge=1)]
    appended: Annotated[int, Field(ge=0)]


class RouteCandidate(Contract):
    unit_id: Id
    unit_type: UnitType
    unit_status: UnitStatus
    route: Route


class RouteCandidates(Contract):
    """Fastest road route from each unit to an incident under current flood closures.

    Informational only: eligibility, locks and allocation remain the solver's job.
    """

    session_id: Id
    incident_id: Id
    as_of_sequence: Annotated[int, Field(ge=1)]
    flood_version: Annotated[int, Field(ge=0)]
    graph_version: str
    routing_policy_version: str
    candidates: list[RouteCandidate]


# --- WebSocket /ws/events (0005) --------------------------------------------------------


class WsHello(Contract):
    type: Literal["hello"]
    session_id: Id
    head_sequence: Annotated[int, Field(ge=0)]
    schema_version: SchemaVersion


class WsSubscribe(Contract):
    type: Literal["subscribe"]
    session_id: Id
    after_sequence: Annotated[int, Field(ge=0)]


class WsEvent(Contract):
    type: Literal["event"]
    event: EventEnvelope


class WsHeartbeat(Contract):
    type: Literal["heartbeat"]
    head_sequence: Annotated[int, Field(ge=0)]


class WsSnapshotRequired(Contract):
    type: Literal["snapshot_required"]
    session_id: Id


class WsCaughtUp(Contract):
    """Server confirms backlog delivery; clients enable commands only after this."""

    type: Literal["caught_up"]
    head_sequence: Annotated[int, Field(ge=0)]


WsServerMessage = Annotated[
    WsHello | WsEvent | WsHeartbeat | WsSnapshotRequired | WsCaughtUp,
    Field(discriminator="type"),
]
