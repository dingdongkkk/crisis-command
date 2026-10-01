"""v1.0 enumerations (decision record 0001). Values are wire strings."""

from enum import StrEnum


class UnitType(StrEnum):
    ALS = "als"
    BLS = "bls"
    FIRE = "fire"
    BOAT = "boat"
    TOW = "tow"


class UnitStatus(StrEnum):
    AVAILABLE = "available"
    EN_ROUTE = "en_route"
    ON_SCENE = "on_scene"
    TRANSPORTING = "transporting"
    AT_FACILITY = "at_facility"
    RETURNING = "returning"
    BROKEN_DOWN = "broken_down"
    OUT_OF_SERVICE = "out_of_service"
    OFF_DUTY = "off_duty"


class NeedType(StrEnum):
    ALS = "als"
    BLS = "bls"
    FIRE = "fire"
    WATER_RESCUE = "water_rescue"
    TOW = "tow"
    SHELTER_PLACES = "shelter_places"


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentCategory(StrEnum):
    EMERGENCY = "emergency"
    NON_EMERGENCY_ASSIST = "non_emergency_assist"
    INFORMATION_REQUEST = "information_request"


class IncidentStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MERGED_DUPLICATE = "merged_duplicate"


class FactValue(StrEnum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class FactSource(StrEnum):
    CALLER_STRUCTURED = "caller_structured"
    RULE_ADAPTER = "rule_adapter"
    MODEL_ADAPTER = "model_adapter"
    OPERATOR = "operator"
    MEDICAL_PROFILE = "medical_profile"


class CountStatus(StrEnum):
    KNOWN = "known"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class NeedBasis(StrEnum):
    CONFIRMED = "confirmed"
    PROVISIONAL_UNKNOWN = "provisional_unknown"


class PlanState(StrEnum):
    COMPUTING = "computing"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    APPROVED = "approved"
    DISPATCHING = "dispatching"
    DISPATCHED_SIMULATED = "dispatched_simulated"
    DISPATCH_PARTIAL_FAILED = "dispatch_partial_failed"
    FAILED = "failed"


class RouteStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"
    PROVIDER_ERROR = "provider_error"


class AssignmentRole(StrEnum):
    PRIMARY = "primary"
    BRIDGE = "bridge"


class LockReason(StrEnum):
    ON_SCENE = "on_scene"
    TRANSPORTING = "transporting"
    NEAR_ARRIVAL = "near_arrival"


class FlagSeverity(StrEnum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class OverrideKind(StrEnum):
    PIN = "pin"
    FORBID = "forbid"
    HOLD_UNIT = "hold_unit"
    APPROVE_BLS_BRIDGE = "approve_bls_bridge"
    DOWNGRADE_NEED = "downgrade_need"
    REVOKE = "revoke"


class OverrideStatus(StrEnum):
    ACTIVE = "active"
    REJECTED = "rejected"
    INVALIDATED = "invalidated"
    REVOKED = "revoked"


class ActorKind(StrEnum):
    OPERATOR = "operator"
    CALLER_SIM = "caller_sim"
    SYSTEM = "system"
    SOLVER = "solver"
    WATCHDOG = "watchdog"
    RULE_ADAPTER = "rule_adapter"
    MODEL_ADAPTER = "model_adapter"


class CoverageStatus(StrEnum):
    COVERED = "covered"
    UNCOVERED = "uncovered"
    COVERAGE_UNKNOWN = "coverage_unknown"


class DispatchAction(StrEnum):
    ASSIGN = "assign"
    RELEASE = "release"
    HOSPITAL_PRE_ALERT = "hospital_pre_alert"


class DispatchState(StrEnum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ObjectiveTier(StrEnum):
    UNMET_CRITICAL = "unmet_critical"
    UNMET_HIGH = "unmet_high"
    UNMET_MEDIUM = "unmet_medium"
    UNMET_LOW = "unmet_low"
    WAITING_COST = "waiting_cost"
    OPERATING_COST = "operating_cost"


class SolverStatus(StrEnum):
    OPTIMAL = "OPTIMAL"
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"
    UNKNOWN = "UNKNOWN"
    MODEL_INVALID = "MODEL_INVALID"
    FALLBACK = "FALLBACK"


# Eligibility table from 0003: need type -> unit types that may satisfy it as primary.
ELIGIBLE_UNIT_TYPES: dict[NeedType, frozenset[UnitType]] = {
    NeedType.ALS: frozenset({UnitType.ALS}),
    NeedType.BLS: frozenset({UnitType.BLS, UnitType.ALS}),
    NeedType.FIRE: frozenset({UnitType.FIRE}),
    NeedType.WATER_RESCUE: frozenset({UnitType.BOAT}),
    NeedType.TOW: frozenset({UnitType.TOW}),
    NeedType.SHELTER_PLACES: frozenset(),
}
