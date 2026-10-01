"""Event envelope and closed payloads for the v1.0 catalog (0005).

``affects_planning`` is fixed by the catalog and validated, never chosen by a caller.
Payloads are closed models carrying IDs, enums, numbers, coordinates and evidence
offsets only; free text and medical profile values are rejected before type checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal, Union

from pydantic import Field, TypeAdapter, create_model, model_validator
from pydantic_core import PydanticCustomError

from .common import (
    Code,
    Contract,
    Id,
    Point,
    SchemaVersion,
    Seconds,
    Sequence,
    UtcTimestamp,
    Uuid,
    Version,
)
from .entities import (
    Actor,
    FloodZone,
    Incident,
    Override,
    Report,
    TriageFact,
    TriageFacts,
    Unit,
)
from .enums import DispatchAction, IncidentCategory, OverrideKind, UnitStatus
from .plan import Plan
from .state import DispatchCommand, StateSnapshot

# Keys that would smuggle caller free text or profile values into the immutable log.
FORBIDDEN_PAYLOAD_KEYS = frozenset(
    {"text", "raw_text", "transcript", "caller_text", "profile_values", "medical_history"}
)


class OverrideConflict(Contract):
    code: Code
    unit_id: Id | None = None
    override_id: Id | None = None
    detail: str


class DesiredAssignment(Contract):
    unit_id: Id
    assignment_id: Id
    desired_revision: Annotated[int, Field(ge=0)]


class UnitPlanningState(Contract):
    unit_id: Id
    position: Point
    remaining_route_s: Seconds | None
    lock: Literal["on_scene", "transporting", "near_arrival"] | None


# --- Planning-relevant payloads --------------------------------------------------------


class SessionStartedPayload(Contract):
    fixture: str
    seed: int
    initial_state: StateSnapshot


class ReportReceivedPayload(Contract):
    report: Report


class TriageFactsExtractedPayload(Contract):
    triage_facts: TriageFacts


class TriageFactConfirmedPayload(Contract):
    incident_id: Id
    fact: TriageFact


class IncidentPayload(Contract):
    incident: Incident


class IncidentCategoryChangedPayload(Contract):
    incident: Incident
    from_category: IncidentCategory
    reason: Code
    triggering_fact_keys: list[str]


class ReportLinkedToIncidentPayload(Contract):
    report_id: Id
    incident_id: Id
    resolution: Literal["linked", "kept_separate"]


class IncidentResolvedPayload(Contract):
    incident_id: Id
    invalidates_assignment_ids: list[Id]


class UnitStatusChangedPayload(Contract):
    unit: Unit
    invalidates_assignment_ids: list[Id]


class PlanningTickCommittedPayload(Contract):
    tick_sim_time_s: Seconds
    units: list[UnitPlanningState]


class FloodZoneUpdatedPayload(Contract):
    flood: FloodZone


class RoadClosureUpdatedPayload(Contract):
    closure_id: Id
    version: Version
    closed: bool
    geometry: Any


class FacilityCapacityUpdatedPayload(Contract):
    facility_id: Id
    ed_beds_available: Annotated[int, Field(ge=0)] | None = None
    occupied_persons: Annotated[int, Field(ge=0)] | None = None


class OverridePayload(Contract):
    override: Override


class OverrideEndedPayload(Contract):
    override_id: Id
    reason: Code


class PlanApprovedPayload(Contract):
    plan_id: Id
    version: Version
    based_on_planning_sequence: Annotated[int, Field(ge=1)]
    acknowledged_flag_ids: list[Id]
    outbox_keys: list[Id]
    desired_assignments: list[DesiredAssignment]
    note_present: bool | None = None


class SimulatedDispatchSentPayload(Contract):
    outbox_key: Id
    action: DispatchAction
    unit_id: Id | None = None
    assignment_id: Id
    unit_after: Unit | None = None
    simulated: Literal[True]


# --- Non-planning payloads -------------------------------------------------------------


class UnitPositionObservedPayload(Contract):
    unit_id: Id
    position: Point
    observed_sim_time_s: Seconds


class EscalatedToHumanPayload(Contract):
    incident_id: Id
    reasons: Annotated[list[Code], Field(min_length=1)]


class DuplicateCandidateFlaggedPayload(Contract):
    report_id: Id
    candidate_incident_id: Id
    reasons: list[Code]


class PlanProposedPayload(Contract):
    plan: Plan


class PlanSupersededPayload(Contract):
    plan_id: Id
    superseded_by_plan_id: Id | None
    reason: Code


class PlanRevalidatedPayload(Contract):
    plan_id: Id
    checked_planning_sequence: Annotated[int, Field(ge=1)]
    checked_sim_time_s: Seconds


class PlanFailedPayload(Contract):
    plan_id: Id
    based_on_planning_sequence: Annotated[int, Field(ge=1)]
    reasons: list[Code]


class ApprovalRejectedPayload(Contract):
    plan_id: Id
    code: Code


class OverrideRejectedPayload(Contract):
    override_id: Id
    kind: OverrideKind
    unit_id: Id | None = None
    need_id: Id | None = None
    incident_id: Id | None = None
    bridges_need_id: Id | None = None
    conflicts: Annotated[list[OverrideConflict], Field(min_length=1)]


class SimulatedDispatchQueuedPayload(Contract):
    command: DispatchCommand


class SimulatedDispatchEndedPayload(Contract):
    outbox_key: Id
    reason: Code
    attempts: Annotated[int, Field(ge=0)] | None = None


class MedicalProfileAccessPayload(Contract):
    """Audit record: field *names* only, never profile values."""

    incident_id: Id
    profile_ref: Id
    granted_fields: list[Literal["conditions", "medications", "allergies", "emergency_contacts"]]
    reason: Code | None = None


class HospitalPreAlertSimulatedPayload(Contract):
    outbox_key: Id
    hospital_id: Id
    incident_id: Id
    capability_needed: Code | None = None
    simulated: Literal[True]


class ModelAdapterDegradedPayload(Contract):
    adapter: Literal["model_adapter", "routing_provider", "solver"]
    cause: Code


EVENT_CATALOG: dict[str, tuple[bool, type[Contract]]] = {
    # affects_planning = True
    "SessionStarted": (True, SessionStartedPayload),
    "ReportReceived": (True, ReportReceivedPayload),
    "TriageFactsExtracted": (True, TriageFactsExtractedPayload),
    "TriageFactConfirmed": (True, TriageFactConfirmedPayload),
    "IncidentCreated": (True, IncidentPayload),
    "IncidentAssessed": (True, IncidentPayload),
    "IncidentCategoryChanged": (True, IncidentCategoryChangedPayload),
    "ReportLinkedToIncident": (True, ReportLinkedToIncidentPayload),
    "IncidentResolved": (True, IncidentResolvedPayload),
    "UnitStatusChanged": (True, UnitStatusChangedPayload),
    "PlanningTickCommitted": (True, PlanningTickCommittedPayload),
    "FloodZoneUpdated": (True, FloodZoneUpdatedPayload),
    "RoadClosureUpdated": (True, RoadClosureUpdatedPayload),
    "FacilityCapacityUpdated": (True, FacilityCapacityUpdatedPayload),
    "OverrideAccepted": (True, OverridePayload),
    "OverrideInvalidated": (True, OverrideEndedPayload),
    "OverrideRevoked": (True, OverrideEndedPayload),
    "PlanApproved": (True, PlanApprovedPayload),
    "SimulatedDispatchSent": (True, SimulatedDispatchSentPayload),
    # affects_planning = False
    "UnitPositionObserved": (False, UnitPositionObservedPayload),
    "EscalatedToHuman": (False, EscalatedToHumanPayload),
    "DuplicateCandidateFlagged": (False, DuplicateCandidateFlaggedPayload),
    "PlanProposed": (False, PlanProposedPayload),
    "PlanSuperseded": (False, PlanSupersededPayload),
    "PlanRevalidated": (False, PlanRevalidatedPayload),
    "PlanFailed": (False, PlanFailedPayload),
    "ApprovalRejected": (False, ApprovalRejectedPayload),
    "OverrideRejected": (False, OverrideRejectedPayload),
    "SimulatedDispatchQueued": (False, SimulatedDispatchQueuedPayload),
    "SimulatedDispatchCancelled": (False, SimulatedDispatchEndedPayload),
    "SimulatedDispatchFailed": (False, SimulatedDispatchEndedPayload),
    "MedicalProfileAccessGranted": (False, MedicalProfileAccessPayload),
    "MedicalProfileAccessDenied": (False, MedicalProfileAccessPayload),
    "HospitalPreAlertSimulated": (False, HospitalPreAlertSimulatedPayload),
    "ModelAdapterDegraded": (False, ModelAdapterDegradedPayload),
}


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            k in FORBIDDEN_PAYLOAD_KEYS or _contains_forbidden_key(v) for k, v in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_key(v) for v in value)
    return False


class EnvelopeBase(Contract):
    """Fields shared by every event; concrete variants fix ``event_type`` and ``payload``."""

    schema_version: SchemaVersion
    event_id: Uuid
    session_id: Id
    sequence: Sequence
    aggregate_type: Annotated[str, Field(pattern=r"^[a-z_]+$")]
    aggregate_id: Id
    occurred_at: UtcTimestamp
    sim_time_s: Seconds
    actor: Actor
    correlation_id: Id
    causation_id: Uuid | None
    idempotency_key: Annotated[str, Field(min_length=1, max_length=200)] | None
    affects_planning: bool
    # Narrowed to a Literal and a concrete payload model by each catalog variant.
    event_type: str
    payload: Contract

    @model_validator(mode="before")
    @classmethod
    def _no_raw_text(cls, data: Any) -> Any:
        if isinstance(data, dict) and _contains_forbidden_key(data.get("payload")):
            raise PydanticCustomError(
                "RAW_TEXT_FORBIDDEN", "events carry text references and hashes, never raw text"
            )
        return data

    @model_validator(mode="after")
    def _catalog_flag(self) -> EnvelopeBase:
        if self.affects_planning != EVENT_CATALOG[self.event_type][0]:
            raise PydanticCustomError(
                "AFFECTS_PLANNING_MISMATCH", "affects_planning is fixed by the event catalog"
            )
        return self


def _variant(event_type: str, payload: type[Contract]) -> type[EnvelopeBase]:
    model: type[EnvelopeBase] = create_model(
        f"{event_type}Event",
        __base__=EnvelopeBase,
        event_type=(Literal[event_type], ...),
        payload=(payload, ...),
    )
    return model


EVENT_VARIANTS: dict[str, type[EnvelopeBase]] = {
    name: _variant(name, payload) for name, (_, payload) in EVENT_CATALOG.items()
}

if TYPE_CHECKING:
    EventEnvelope = EnvelopeBase
else:
    EventEnvelope = Annotated[
        Union[tuple(EVENT_VARIANTS.values())],  # noqa: UP007 - built from the catalog
        Field(discriminator="event_type"),
    ]
    """Discriminated union of every catalog event; validate with ``EVENT_ADAPTER``."""

EVENT_ADAPTER: TypeAdapter[EnvelopeBase] = TypeAdapter(EventEnvelope)

UNIT_STATUSES_WITHOUT_NEW_TASKS = frozenset(
    {UnitStatus.BROKEN_DOWN, UnitStatus.OUT_OF_SERVICE, UnitStatus.OFF_DUTY}
)
