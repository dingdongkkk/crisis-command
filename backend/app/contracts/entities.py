"""World entities: reports, triage facts, incidents, fleet, facilities, geography (0001-0003)."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field, model_validator
from pydantic_core import PydanticCustomError

from .common import (
    Beds,
    Code,
    Contract,
    Id,
    LineString,
    Metres,
    Persons,
    Point,
    Polygon,
    ReasonFact,
    Seconds,
    UtcTimestamp,
    Version,
)
from .enums import (
    ActorKind,
    CountStatus,
    FactSource,
    FactValue,
    IncidentCategory,
    IncidentStatus,
    NeedBasis,
    NeedType,
    OverrideKind,
    OverrideStatus,
    RouteStatus,
    Severity,
    UnitStatus,
    UnitType,
)

# --- Reports ----------------------------------------------------------------------------


class TextRef(Contract):
    """Reference to caller text held in the separate, revocable report store (0005)."""

    store: Literal["report_text"]
    report_id: Id | None = None
    text_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    length_chars: Persons


class Report(Contract):
    report_id: Id
    received_sim_time_s: Seconds
    received_at: UtcTimestamp
    channel: Literal["text_sim", "structured_sim"]
    text_ref: TextRef
    location: Point
    location_source: Literal["caller_stated", "operator_entered", "fixture"]
    linked_incident_id: Id | None = None


# --- Triage (0002) ----------------------------------------------------------------------


class EvidenceSpan(Contract):
    report_id: Id
    start: Persons
    end: Persons

    @model_validator(mode="after")
    def _ordered(self) -> EvidenceSpan:
        if self.end <= self.start:
            raise PydanticCustomError("EVIDENCE_SPAN_INVALID", "evidence end must follow start")
        return self


class FactCount(Contract):
    value: Persons | None
    status: CountStatus

    @model_validator(mode="after")
    def _unknown_is_null(self) -> FactCount:
        if self.status is CountStatus.UNKNOWN and self.value is not None:
            raise PydanticCustomError(
                "UNKNOWN_COUNT_MUST_BE_NULL", "an unknown count has value null, never 0"
            )
        if self.status is not CountStatus.UNKNOWN and self.value is None:
            raise PydanticCustomError("COUNT_VALUE_REQUIRED", "a known count needs a value")
        return self


COUNT_FACTS = frozenset({"people_count"})
EXTRACTING_SOURCES = frozenset({FactSource.RULE_ADAPTER, FactSource.MODEL_ADAPTER})


class TriageFact(Contract):
    """Tri-state fact with provenance. ``people_count`` uses ``count`` instead of ``value``."""

    key: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    value: FactValue | None = None
    count: FactCount | None = None
    source: FactSource
    evidence: list[EvidenceSpan]
    updated_sim_time_s: Seconds
    confirmed_by_operator: bool
    conflict: bool | None = None
    coerced_from: FactValue | None = None
    coercion_reason: Code | None = None

    @model_validator(mode="before")
    @classmethod
    def _tri_state(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("key") in COUNT_FACTS:
            if "count" not in data:
                raise PydanticCustomError("FACT_COUNT_REQUIRED", "count facts carry `count`")
            return data
        if "value" not in data:
            raise PydanticCustomError(
                "FACT_VALUE_REQUIRED", "facts are always present; unestablished is 'unknown'"
            )
        if data["value"] not in {v.value for v in FactValue}:
            raise PydanticCustomError("TRISTATE_REQUIRED", "fact value is yes, no or unknown")
        return data

    @model_validator(mode="after")
    def _evidence_for_assertions(self) -> TriageFact:
        if self.key in COUNT_FACTS:
            if self.value is not None:
                raise PydanticCustomError("FACT_COUNT_REQUIRED", "count facts use `count` only")
            return self
        if self.count is not None:
            raise PydanticCustomError("FACT_VALUE_REQUIRED", "binary facts use `value` only")
        # 0002 rule 2: an extracted yes/no must cite supporting spans; otherwise store unknown.
        if (
            self.source in EXTRACTING_SOURCES
            and self.value is not FactValue.UNKNOWN
            and not self.evidence
        ):
            raise PydanticCustomError(
                "ASSERTION_WITHOUT_EVIDENCE",
                "extracted yes/no needs an evidence span; store unknown instead",
            )
        return self


class QuestionAsked(Contract):
    fact_key: str
    asked_sim_time_s: Seconds
    answer: FactValue | None = None


class Escalation(Contract):
    escalated: bool
    reasons: list[Code]
    sim_time_s: Seconds | None = None


class TriageFacts(Contract):
    incident_id: Id
    policy_version: str
    facts: list[TriageFact]
    applicable_facts: list[str]
    questions_asked: list[QuestionAsked]
    escalation: Escalation


# --- Incidents --------------------------------------------------------------------------


class Need(Contract):
    need_id: Id
    type: NeedType
    quantity: Annotated[int, Field(ge=1)]
    basis: NeedBasis
    reasons: list[ReasonFact]


class Incident(Contract):
    incident_id: Id
    category: IncidentCategory
    kind: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]
    severity: Severity
    assumed_facts: list[str]
    location: Point
    created_sim_time_s: Seconds
    status: IncidentStatus
    report_ids: list[Id]
    needs: list[Need]
    duplicate_candidate_of: list[Id]

    @model_validator(mode="after")
    def _non_emergency_has_no_unit_needs(self) -> Incident:
        if self.category is not IncidentCategory.EMERGENCY and self.needs:
            raise PydanticCustomError(
                "NON_EMERGENCY_HAS_NEEDS", "non-emergency incidents consume no emergency units"
            )
        return self


# --- Fleet ------------------------------------------------------------------------------


class CurrentTask(Contract):
    assignment_id: Id
    incident_id: Id
    need_id: Id | None = None


class Unit(Contract):
    unit_id: Id
    display_name: str
    type: UnitType
    status: UnitStatus
    position: Point
    position_sim_time_s: Seconds
    home_zone_id: Id
    current_task: CurrentTask | None
    capacity_persons: Persons
    desired_revision: Annotated[int, Field(ge=0)] | None = None


# --- Facilities -------------------------------------------------------------------------


class Hospital(Contract):
    facility_id: Id
    kind: Literal["hospital"]
    display_name: str
    location: Point
    capabilities: list[Literal["emergency", "cardiac", "trauma", "burns", "paediatric"]]
    ed_beds_available: Beds


class Shelter(Contract):
    facility_id: Id
    kind: Literal["shelter"]
    display_name: str
    location: Point
    capacity_persons: Persons
    occupied_persons: Persons

    @model_validator(mode="after")
    def _occupancy(self) -> Shelter:
        if self.occupied_persons > self.capacity_persons:
            raise PydanticCustomError("CAPACITY_EXCEEDED", "occupied exceeds capacity")
        return self


Facility = Annotated[Hospital | Shelter, Field(discriminator="kind")]

# --- Geography and routes ---------------------------------------------------------------


class FloodZone(Contract):
    flood_id: Id
    version: Version
    effective_sim_time_s: Seconds
    closes_roads: bool
    geometry: Polygon
    source: Literal["synthetic_progression", "operator_entered"]


class ReserveZone(Contract):
    zone_id: Id
    reference_point: Point
    required_types: list[UnitType]
    coverage_eta_s: Seconds
    geometry: Polygon | None = None


class Route(Contract):
    """A recorded route result. Unavailable routes never carry an estimate (0003 H5)."""

    route_id: Id
    from_: Point = Field(alias="from")
    to: Point
    route_status: RouteStatus
    provider: Literal["fixture", "ors_directions"]
    flood_version: Annotated[int, Field(ge=0)]
    duration_s: Seconds | None
    distance_m: Metres | None
    geometry: LineString | None
    unavailable_reason: Code | None = None

    @model_validator(mode="after")
    def _no_estimate_without_route(self) -> Route:
        measured = (self.duration_s, self.distance_m, self.geometry)
        if self.route_status is RouteStatus.OK:
            if any(v is None for v in measured):
                raise PydanticCustomError(
                    "ROUTE_INCOMPLETE", "ok routes need duration, distance, geometry"
                )
            if self.unavailable_reason is not None:
                raise PydanticCustomError(
                    "ROUTE_INCOMPLETE", "ok routes have no unavailable_reason"
                )
        else:
            if any(v is not None for v in measured):
                raise PydanticCustomError(
                    "ROUTE_UNAVAILABLE", "an unavailable route cannot carry an ETA or geometry"
                )
            if self.unavailable_reason is None:
                raise PydanticCustomError(
                    "ROUTE_REASON_REQUIRED", "unavailable routes need a reason"
                )
        return self


# --- Overrides and medical profiles -----------------------------------------------------


class Actor(Contract):
    kind: ActorKind
    id: str


class Override(Contract):
    override_id: Id
    kind: OverrideKind
    unit_id: Id | None = None
    need_id: Id | None = None
    incident_id: Id | None = None
    zone_id: Id | None = None
    bridges_need_id: Id | None = None
    replaces_override_id: Id | None = None
    revokes_override_id: Id | None = None
    reason_text: Annotated[str, Field(min_length=1, max_length=280)]
    status: OverrideStatus
    created_by: Actor
    accepted_sequence: Annotated[int, Field(ge=1)] | None = None
    expected_session_id: Id


class Consent(Contract):
    granted: bool
    scope: list[Literal["conditions", "medications", "allergies", "emergency_contacts"]]
    granted_at: UtcTimestamp
    revocable: bool


class AccessRule(Contract):
    requires_caller_is_patient: Literal[True]
    requires_active_incident: Literal[True]
    requires_operator_reason: Literal[True]


class MedicalProfileConsent(Contract):
    """Consent metadata only. Profile values live in a separate store and never in events."""

    profile_ref: Id
    subject_ref: Id
    consent: Consent
    access_rule: AccessRule
    synthetic: Literal[True]
