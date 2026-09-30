/* Generated from contracts/schema/crisis-command.schema.json by npm run gen:contracts. Do not edit. */

/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ActorKind".
 */
export type ActorKind = "operator" | "caller_sim" | "system" | "solver" | "watchdog" | "rule_adapter" | "model_adapter";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactValue".
 */
export type FactValue = "yes" | "no" | "unknown";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "LockReason".
 */
export type LockReason = "on_scene" | "transporting" | "near_arrival";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RouteStatus".
 */
export type RouteStatus = "ok" | "unavailable" | "provider_error";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "AssignmentRole".
 */
export type AssignmentRole = "primary" | "bridge";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CountStatus".
 */
export type CountStatus = "known" | "approximate" | "unknown";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitType".
 */
export type UnitType = "als" | "bls" | "fire" | "boat" | "tow";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CoverageStatus".
 */
export type CoverageStatus = "covered" | "uncovered" | "coverage_unknown";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DispatchAction".
 */
export type DispatchAction = "assign" | "release" | "hospital_pre_alert";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DispatchState".
 */
export type DispatchState = "pending" | "sent" | "cancelled" | "failed";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EventEnvelope".
 */
export type EventEnvelope =
  | SessionStartedEvent
  | ReportReceivedEvent
  | TriageFactsExtractedEvent
  | TriageFactConfirmedEvent
  | IncidentCreatedEvent
  | IncidentAssessedEvent
  | IncidentCategoryChangedEvent
  | ReportLinkedToIncidentEvent
  | IncidentResolvedEvent
  | UnitStatusChangedEvent
  | PlanningTickCommittedEvent
  | FloodZoneUpdatedEvent
  | RoadClosureUpdatedEvent
  | FacilityCapacityUpdatedEvent
  | OverrideAcceptedEvent
  | OverrideInvalidatedEvent
  | OverrideRevokedEvent
  | PlanApprovedEvent
  | SimulatedDispatchSentEvent
  | UnitPositionObservedEvent
  | EscalatedToHumanEvent
  | DuplicateCandidateFlaggedEvent
  | PlanProposedEvent
  | PlanSupersededEvent
  | PlanRevalidatedEvent
  | PlanFailedEvent
  | ApprovalRejectedEvent
  | OverrideRejectedEvent
  | SimulatedDispatchQueuedEvent
  | SimulatedDispatchCancelledEvent
  | SimulatedDispatchFailedEvent
  | MedicalProfileAccessGrantedEvent
  | MedicalProfileAccessDeniedEvent
  | HospitalPreAlertSimulatedEvent
  | ModelAdapterDegradedEvent;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideKind".
 */
export type OverrideKind = "pin" | "forbid" | "hold_unit" | "approve_bls_bridge" | "downgrade_need" | "revoke";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideStatus".
 */
export type OverrideStatus = "active" | "rejected" | "invalidated" | "revoked";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FlagSeverity".
 */
export type FlagSeverity = "critical" | "warning" | "info";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ObjectiveTier".
 */
export type ObjectiveTier =
  "unmet_critical" | "unmet_high" | "unmet_medium" | "unmet_low" | "waiting_cost" | "operating_cost";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SolverStatus".
 */
export type SolverStatus = "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "UNKNOWN" | "MODEL_INVALID" | "FALLBACK";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanState".
 */
export type PlanState =
  | "computing"
  | "proposed"
  | "superseded"
  | "approved"
  | "dispatching"
  | "dispatched_simulated"
  | "dispatch_partial_failed"
  | "failed";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "NeedBasis".
 */
export type NeedBasis = "confirmed" | "provisional_unknown";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Severity".
 */
export type Severity = "critical" | "high" | "medium" | "low";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "NeedType".
 */
export type NeedType = "als" | "bls" | "fire" | "water_rescue" | "tow" | "shelter_places";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCategory".
 */
export type IncidentCategory = "emergency" | "non_emergency_assist" | "information_request";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentStatus".
 */
export type IncidentStatus = "active" | "resolved" | "merged_duplicate";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactSource".
 */
export type FactSource = "caller_structured" | "rule_adapter" | "model_adapter" | "operator" | "medical_profile";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatus".
 */
export type UnitStatus =
  | "available"
  | "en_route"
  | "on_scene"
  | "transporting"
  | "at_facility"
  | "returning"
  | "broken_down"
  | "out_of_service"
  | "off_duty";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsServerMessage".
 */
export type WsServerMessage = WsHello | WsEvent | WsHeartbeat | WsSnapshotRequired | WsCaughtUp;

/**
 * Crisis Command contract schema_version 1.0. Generated from backend/app/contracts; do not edit by hand.
 */
export interface CrisisCommandContracts {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "AccessRule".
 */
export interface AccessRule {
  requires_active_incident: true;
  requires_caller_is_patient: true;
  requires_operator_reason: true;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Actor".
 */
export interface Actor {
  id: string;
  kind: ActorKind;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "AnswerCommand".
 */
export interface AnswerCommand {
  answer: FactValue;
  expected_session_id: string;
  fact_key: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApprovalAccepted".
 */
export interface ApprovalAccepted {
  outbox_keys: string[];
  plan_id: string;
  sequence: number;
  state: "approved" | "dispatched_simulated";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApprovalRejectedEvent".
 */
export interface ApprovalRejectedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "ApprovalRejected";
  idempotency_key: string | null;
  occurred_at: string;
  payload: ApprovalRejectedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApprovalRejectedPayload".
 */
export interface ApprovalRejectedPayload {
  code: string;
  plan_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApproveCommand".
 */
export interface ApproveCommand {
  acknowledged_flag_ids: string[];
  expected_plan_version: number;
  expected_planning_sequence: number;
  expected_session_id: string;
  note?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Assignment".
 */
export interface Assignment {
  assignment_id: string;
  bridges_need_id?: string | null;
  destination_facility_id?: string | null;
  eta_s: number;
  incident_id: string;
  locked: LockReason | null;
  need_id?: string | null;
  onward_route?: Route | null;
  persons?: number | null;
  reasons: ReasonFact[];
  role: AssignmentRole;
  route: Route;
  satisfies_need: boolean;
  unit_id: string;
}
/**
 * A recorded route result. Unavailable routes never carry an estimate (0003 H5).
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Route".
 */
export interface Route {
  distance_m: number | null;
  duration_s: number | null;
  flood_version: number;
  from: Point;
  geometry: LineString | null;
  provider: "fixture" | "ors_directions";
  route_id: string;
  route_status: RouteStatus;
  to: Point;
  unavailable_reason?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Point".
 */
export interface Point {
  /**
   * @minItems 2
   * @maxItems 2
   */
  coordinates: [number, number];
  type: "Point";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "LineString".
 */
export interface LineString {
  /**
   * @minItems 2
   */
  coordinates: [[number, number], [number, number], ...[number, number][]];
  type: "LineString";
}
/**
 * Typed evidence for explanations; templates and models may only restate these.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReasonFact".
 */
export interface ReasonFact {
  code: string;
  params?: {
    [k: string]: string | number | boolean | string[] | null;
  };
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "BridgeCandidate".
 */
export interface BridgeCandidate {
  cost_of_taking: CostOfTaking[];
  eta_s: number;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CostOfTaking".
 */
export interface CostOfTaking {
  delta?: number | null;
  metric: "unmet_need" | "reserve_uncovered" | "already_assigned_same_incident" | "weighted_eta_s";
  need_id?: string | null;
  zone_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Consent".
 */
export interface Consent {
  granted: boolean;
  granted_at: string;
  revocable: boolean;
  scope: ("conditions" | "medications" | "allergies" | "emergency_contacts")[];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Coverage".
 */
export interface Coverage {
  available_unit_ids: string[];
  resource_type: UnitType;
  status: CoverageStatus;
  zone_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CurrentTask".
 */
export interface CurrentTask {
  assignment_id: string;
  incident_id: string;
  need_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoAdvanceCommand".
 */
export interface DemoAdvanceCommand {
  expected_session_id: string;
  to_step: "T+0" | "T+2" | "T+5" | "T+10";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoAdvanceResult".
 */
export interface DemoAdvanceResult {
  appended: number;
  head_sequence: number;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoResetCommand".
 */
export interface DemoResetCommand {
  expected_session_id: string;
  fixture: "demo-bengaluru-v1";
  seed: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoResetResult".
 */
export interface DemoResetResult {
  head_sequence: number;
  session_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DesiredAssignment".
 */
export interface DesiredAssignment {
  assignment_id: string;
  desired_revision: number;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DiffEndpoint".
 */
export interface DiffEndpoint {
  eta_s?: number | null;
  incident_id?: string | null;
  need_id?: string | null;
  state?: ("available" | "assigned" | "held") | null;
  zone_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DiffRow".
 */
export interface DiffRow {
  from: DiffEndpoint;
  reason?: ReasonFact | null;
  to?: DiffEndpoint | null;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DiffTotals".
 */
export interface DiffTotals {
  needs_unmet: number;
  units_added: number;
  units_moved: number;
  units_released: number;
  weighted_eta_delta_s: number;
  zones_uncovered: number;
}
/**
 * Simulated outbox command. ``simulated`` is always true; no real transport exists.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DispatchCommand".
 */
export interface DispatchCommand {
  action: DispatchAction;
  assignment_id: string;
  desired_revision: number;
  incident_id?: string | null;
  outbox_key: string;
  plan_id: string;
  session_id: string;
  simulated: true;
  state: DispatchState;
  unit_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DuplicateCandidateFlaggedEvent".
 */
export interface DuplicateCandidateFlaggedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "DuplicateCandidateFlagged";
  idempotency_key: string | null;
  occurred_at: string;
  payload: DuplicateCandidateFlaggedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DuplicateCandidateFlaggedPayload".
 */
export interface DuplicateCandidateFlaggedPayload {
  candidate_incident_id: string;
  reasons: string[];
  report_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DuplicateResolveCommand".
 */
export interface DuplicateResolveCommand {
  expected_session_id: string;
  reason_text: string;
  resolution: "linked" | "kept_separate";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EscalatedToHumanEvent".
 */
export interface EscalatedToHumanEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "EscalatedToHuman";
  idempotency_key: string | null;
  occurred_at: string;
  payload: EscalatedToHumanPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EscalatedToHumanPayload".
 */
export interface EscalatedToHumanPayload {
  incident_id: string;
  /**
   * @minItems 1
   */
  reasons: [string, ...string[]];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Escalation".
 */
export interface Escalation {
  escalated: boolean;
  reasons: string[];
  sim_time_s?: number | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SessionStartedEvent".
 */
export interface SessionStartedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "SessionStarted";
  idempotency_key: string | null;
  occurred_at: string;
  payload: SessionStartedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SessionStartedPayload".
 */
export interface SessionStartedPayload {
  fixture: string;
  initial_state: StateSnapshot;
  seed: number;
}
/**
 * ``GET /state`` body; also the checkpoint embedded in ``SessionStarted``.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "StateSnapshot".
 */
export interface StateSnapshot {
  active_overrides: Override[];
  approved_plan: Plan | null;
  as_of_sequence: number;
  current_proposal: Plan | null;
  facilities: (Hospital | Shelter)[];
  flood: FloodZone[];
  historical_plans?: Plan[] | null;
  incidents: Incident[];
  outbox: DispatchCommand[];
  planning_sequence: number;
  policy: Policy;
  reports: Report[];
  reserve_zones: ReserveZone[];
  schema_version: string;
  session_id: string;
  sim_time_s: number;
  triage_facts: TriageFacts[];
  units: Unit[];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Override".
 */
export interface Override {
  accepted_sequence?: number | null;
  bridges_need_id?: string | null;
  created_by: Actor;
  expected_session_id: string;
  incident_id?: string | null;
  kind: OverrideKind;
  need_id?: string | null;
  override_id: string;
  reason_text: string;
  replaces_override_id?: string | null;
  revokes_override_id?: string | null;
  status: OverrideStatus;
  unit_id?: string | null;
  zone_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Plan".
 */
export interface Plan {
  assignments: Assignment[];
  based_on_planning_sequence: number;
  coverage: Coverage[];
  created_at: string;
  created_sim_time_s: number;
  diff: PlanDiff;
  facility_allocations: FacilityAllocation[];
  flags: PolicyFlag[];
  plan_id: string;
  policy_version: string;
  schema_version: string;
  session_id: string;
  soft_consequences: SoftConsequence[];
  solver: SolverResult;
  state: PlanState;
  supersedes_approved_plan_id?: string | null;
  unmet_needs: UnmetNeed[];
  version: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanDiff".
 */
export interface PlanDiff {
  added: DiffRow[];
  against_plan_id: string | null;
  changed: DiffRow[];
  newly_unmet: string[];
  released: DiffRow[];
  totals: DiffTotals;
  unchanged_count: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FacilityAllocation".
 */
export interface FacilityAllocation {
  allocation_id: string;
  facility_id: string;
  free_after_persons: number;
  incident_id: string;
  need_id: string;
  persons: number;
  route?: Route | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PolicyFlag".
 */
export interface PolicyFlag {
  code: string;
  flag_id: string;
  incident_id?: string | null;
  message: string;
  need_id?: string | null;
  override_id?: string | null;
  requires_ack: boolean;
  resource_type?: UnitType | null;
  severity: FlagSeverity;
  since_sim_time_s?: number | null;
  zone_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SoftConsequence".
 */
export interface SoftConsequence {
  delta?: number | null;
  metric: "weighted_eta_s" | "reserve_uncovered" | "unmet_need";
  need_id?: string | null;
  override_id?: string | null;
  zone_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SolverResult".
 */
export interface SolverResult {
  completed_tiers: ObjectiveTier[];
  engine: "ortools_cp_sat" | "greedy_fallback";
  lexicographic_complete: boolean;
  /**
   * @minItems 6
   * @maxItems 6
   */
  objective_vector: [number, number, number, number, number, number];
  seed: number;
  status: SolverStatus;
  tie_break_complete: boolean;
  wall_time_ms: number;
  workers: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnmetNeed".
 */
export interface UnmetNeed {
  basis: NeedBasis;
  /**
   * @maxItems 3
   */
  bridge_candidates?:
    [] | [BridgeCandidate] | [BridgeCandidate, BridgeCandidate] | [BridgeCandidate, BridgeCandidate, BridgeCandidate];
  incident_id: string;
  need_id: string;
  quantity_unmet: number;
  reasons: ReasonFact[];
  severity: Severity;
  type: NeedType;
  waiting_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Hospital".
 */
export interface Hospital {
  capabilities: ("emergency" | "cardiac" | "trauma" | "burns" | "paediatric")[];
  display_name: string;
  ed_beds_available: number;
  facility_id: string;
  kind: "hospital";
  location: Point;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Shelter".
 */
export interface Shelter {
  capacity_persons: number;
  display_name: string;
  facility_id: string;
  kind: "shelter";
  location: Point;
  occupied_persons: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodZone".
 */
export interface FloodZone {
  closes_roads: boolean;
  effective_sim_time_s: number;
  flood_id: string;
  geometry: Polygon;
  source: "synthetic_progression" | "operator_entered";
  version: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Polygon".
 */
export interface Polygon {
  /**
   * @minItems 1
   */
  coordinates: [[number, number][], ...[number, number][][]];
  type: "Polygon";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Incident".
 */
export interface Incident {
  assumed_facts: string[];
  category: IncidentCategory;
  created_sim_time_s: number;
  duplicate_candidate_of: string[];
  incident_id: string;
  kind: string;
  location: Point;
  needs: Need[];
  report_ids: string[];
  severity: Severity;
  status: IncidentStatus;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Need".
 */
export interface Need {
  basis: NeedBasis;
  need_id: string;
  quantity: number;
  reasons: ReasonFact[];
  type: NeedType;
}
/**
 * Demonstration policy; values are not clinical or operational standards.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Policy".
 */
export interface Policy {
  costs: PolicyCosts;
  dangerous_values: {
    [k: string]: "yes" | "no";
  };
  limits: PolicyLimits;
  max_debounce_ms: number;
  near_arrival_lock_s: number;
  objective_tiers: ObjectiveTier[];
  planning_tick_s: number;
  policy_version: string;
  severity_weights: {
    [k: string]: number;
  };
  solver_budget_ms: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PolicyCosts".
 */
export interface PolicyCosts {
  als_on_bls: number;
  reassignment: number;
  reserve_shortfall: number;
  travel_cap_s: number;
  waiting_cap_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PolicyLimits".
 */
export interface PolicyLimits {
  demand_quanta: number;
  need_records: number;
  reserve_pairs: number;
  units: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Report".
 */
export interface Report {
  channel: "text_sim" | "structured_sim";
  linked_incident_id?: string | null;
  location: Point;
  location_source: "caller_stated" | "operator_entered" | "fixture";
  received_at: string;
  received_sim_time_s: number;
  report_id: string;
  text_ref: TextRef;
}
/**
 * Reference to caller text held in the separate, revocable report store (0005).
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TextRef".
 */
export interface TextRef {
  length_chars: number;
  report_id?: string | null;
  store: "report_text";
  text_sha256: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReserveZone".
 */
export interface ReserveZone {
  coverage_eta_s: number;
  geometry?: Polygon | null;
  reference_point: Point;
  required_types: UnitType[];
  zone_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFacts".
 */
export interface TriageFacts {
  applicable_facts: string[];
  escalation: Escalation;
  facts: TriageFact[];
  incident_id: string;
  policy_version: string;
  questions_asked: QuestionAsked[];
}
/**
 * Tri-state fact with provenance. ``people_count`` uses ``count`` instead of ``value``.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFact".
 */
export interface TriageFact {
  coerced_from?: FactValue | null;
  coercion_reason?: string | null;
  confirmed_by_operator: boolean;
  conflict?: boolean | null;
  count?: FactCount | null;
  evidence: EvidenceSpan[];
  key: string;
  source: FactSource;
  updated_sim_time_s: number;
  value?: FactValue | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactCount".
 */
export interface FactCount {
  status: CountStatus;
  value: number | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EvidenceSpan".
 */
export interface EvidenceSpan {
  end: number;
  report_id: string;
  start: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "QuestionAsked".
 */
export interface QuestionAsked {
  answer?: FactValue | null;
  asked_sim_time_s: number;
  fact_key: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Unit".
 */
export interface Unit {
  capacity_persons: number;
  current_task: CurrentTask | null;
  desired_revision?: number | null;
  display_name: string;
  home_zone_id: string;
  position: Point;
  position_sim_time_s: number;
  status: UnitStatus;
  type: UnitType;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportReceivedEvent".
 */
export interface ReportReceivedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "ReportReceived";
  idempotency_key: string | null;
  occurred_at: string;
  payload: ReportReceivedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportReceivedPayload".
 */
export interface ReportReceivedPayload {
  report: Report;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactsExtractedEvent".
 */
export interface TriageFactsExtractedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "TriageFactsExtracted";
  idempotency_key: string | null;
  occurred_at: string;
  payload: TriageFactsExtractedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactsExtractedPayload".
 */
export interface TriageFactsExtractedPayload {
  triage_facts: TriageFacts;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactConfirmedEvent".
 */
export interface TriageFactConfirmedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "TriageFactConfirmed";
  idempotency_key: string | null;
  occurred_at: string;
  payload: TriageFactConfirmedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactConfirmedPayload".
 */
export interface TriageFactConfirmedPayload {
  fact: TriageFact;
  incident_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCreatedEvent".
 */
export interface IncidentCreatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "IncidentCreated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: IncidentPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentPayload".
 */
export interface IncidentPayload {
  incident: Incident;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentAssessedEvent".
 */
export interface IncidentAssessedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "IncidentAssessed";
  idempotency_key: string | null;
  occurred_at: string;
  payload: IncidentPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCategoryChangedEvent".
 */
export interface IncidentCategoryChangedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "IncidentCategoryChanged";
  idempotency_key: string | null;
  occurred_at: string;
  payload: IncidentCategoryChangedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCategoryChangedPayload".
 */
export interface IncidentCategoryChangedPayload {
  from_category: IncidentCategory;
  incident: Incident;
  reason: string;
  triggering_fact_keys: string[];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportLinkedToIncidentEvent".
 */
export interface ReportLinkedToIncidentEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "ReportLinkedToIncident";
  idempotency_key: string | null;
  occurred_at: string;
  payload: ReportLinkedToIncidentPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportLinkedToIncidentPayload".
 */
export interface ReportLinkedToIncidentPayload {
  incident_id: string;
  report_id: string;
  resolution: "linked" | "kept_separate";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentResolvedEvent".
 */
export interface IncidentResolvedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "IncidentResolved";
  idempotency_key: string | null;
  occurred_at: string;
  payload: IncidentResolvedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentResolvedPayload".
 */
export interface IncidentResolvedPayload {
  incident_id: string;
  invalidates_assignment_ids: string[];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusChangedEvent".
 */
export interface UnitStatusChangedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "UnitStatusChanged";
  idempotency_key: string | null;
  occurred_at: string;
  payload: UnitStatusChangedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusChangedPayload".
 */
export interface UnitStatusChangedPayload {
  invalidates_assignment_ids: string[];
  unit: Unit;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanningTickCommittedEvent".
 */
export interface PlanningTickCommittedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "PlanningTickCommitted";
  idempotency_key: string | null;
  occurred_at: string;
  payload: PlanningTickCommittedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanningTickCommittedPayload".
 */
export interface PlanningTickCommittedPayload {
  tick_sim_time_s: number;
  units: UnitPlanningState[];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitPlanningState".
 */
export interface UnitPlanningState {
  lock: ("on_scene" | "transporting" | "near_arrival") | null;
  position: Point;
  remaining_route_s: number | null;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodZoneUpdatedEvent".
 */
export interface FloodZoneUpdatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "FloodZoneUpdated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: FloodZoneUpdatedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodZoneUpdatedPayload".
 */
export interface FloodZoneUpdatedPayload {
  flood: FloodZone;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RoadClosureUpdatedEvent".
 */
export interface RoadClosureUpdatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "RoadClosureUpdated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: RoadClosureUpdatedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RoadClosureUpdatedPayload".
 */
export interface RoadClosureUpdatedPayload {
  closed: boolean;
  closure_id: string;
  geometry: unknown;
  version: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FacilityCapacityUpdatedEvent".
 */
export interface FacilityCapacityUpdatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "FacilityCapacityUpdated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: FacilityCapacityUpdatedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FacilityCapacityUpdatedPayload".
 */
export interface FacilityCapacityUpdatedPayload {
  ed_beds_available?: number | null;
  facility_id: string;
  occupied_persons?: number | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideAcceptedEvent".
 */
export interface OverrideAcceptedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "OverrideAccepted";
  idempotency_key: string | null;
  occurred_at: string;
  payload: OverridePayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverridePayload".
 */
export interface OverridePayload {
  override: Override;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideInvalidatedEvent".
 */
export interface OverrideInvalidatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "OverrideInvalidated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: OverrideEndedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideEndedPayload".
 */
export interface OverrideEndedPayload {
  override_id: string;
  reason: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRevokedEvent".
 */
export interface OverrideRevokedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "OverrideRevoked";
  idempotency_key: string | null;
  occurred_at: string;
  payload: OverrideEndedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanApprovedEvent".
 */
export interface PlanApprovedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "PlanApproved";
  idempotency_key: string | null;
  occurred_at: string;
  payload: PlanApprovedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanApprovedPayload".
 */
export interface PlanApprovedPayload {
  acknowledged_flag_ids: string[];
  based_on_planning_sequence: number;
  desired_assignments: DesiredAssignment[];
  note_present?: boolean | null;
  outbox_keys: string[];
  plan_id: string;
  version: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchSentEvent".
 */
export interface SimulatedDispatchSentEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "SimulatedDispatchSent";
  idempotency_key: string | null;
  occurred_at: string;
  payload: SimulatedDispatchSentPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchSentPayload".
 */
export interface SimulatedDispatchSentPayload {
  action: DispatchAction;
  assignment_id: string;
  outbox_key: string;
  simulated: true;
  unit_after?: Unit | null;
  unit_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitPositionObservedEvent".
 */
export interface UnitPositionObservedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "UnitPositionObserved";
  idempotency_key: string | null;
  occurred_at: string;
  payload: UnitPositionObservedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitPositionObservedPayload".
 */
export interface UnitPositionObservedPayload {
  observed_sim_time_s: number;
  position: Point;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanProposedEvent".
 */
export interface PlanProposedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "PlanProposed";
  idempotency_key: string | null;
  occurred_at: string;
  payload: PlanProposedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanProposedPayload".
 */
export interface PlanProposedPayload {
  plan: Plan;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanSupersededEvent".
 */
export interface PlanSupersededEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "PlanSuperseded";
  idempotency_key: string | null;
  occurred_at: string;
  payload: PlanSupersededPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanSupersededPayload".
 */
export interface PlanSupersededPayload {
  plan_id: string;
  reason: string;
  superseded_by_plan_id: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanRevalidatedEvent".
 */
export interface PlanRevalidatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "PlanRevalidated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: PlanRevalidatedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanRevalidatedPayload".
 */
export interface PlanRevalidatedPayload {
  checked_planning_sequence: number;
  checked_sim_time_s: number;
  plan_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanFailedEvent".
 */
export interface PlanFailedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "PlanFailed";
  idempotency_key: string | null;
  occurred_at: string;
  payload: PlanFailedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanFailedPayload".
 */
export interface PlanFailedPayload {
  based_on_planning_sequence: number;
  plan_id: string;
  reasons: string[];
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRejectedEvent".
 */
export interface OverrideRejectedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "OverrideRejected";
  idempotency_key: string | null;
  occurred_at: string;
  payload: OverrideRejectedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRejectedPayload".
 */
export interface OverrideRejectedPayload {
  bridges_need_id?: string | null;
  /**
   * @minItems 1
   */
  conflicts: [OverrideConflict, ...OverrideConflict[]];
  incident_id?: string | null;
  kind: OverrideKind;
  need_id?: string | null;
  override_id: string;
  unit_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideConflict".
 */
export interface OverrideConflict {
  code: string;
  detail: string;
  override_id?: string | null;
  unit_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchQueuedEvent".
 */
export interface SimulatedDispatchQueuedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "SimulatedDispatchQueued";
  idempotency_key: string | null;
  occurred_at: string;
  payload: SimulatedDispatchQueuedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchQueuedPayload".
 */
export interface SimulatedDispatchQueuedPayload {
  command: DispatchCommand;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchCancelledEvent".
 */
export interface SimulatedDispatchCancelledEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "SimulatedDispatchCancelled";
  idempotency_key: string | null;
  occurred_at: string;
  payload: SimulatedDispatchEndedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchEndedPayload".
 */
export interface SimulatedDispatchEndedPayload {
  attempts?: number | null;
  outbox_key: string;
  reason: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchFailedEvent".
 */
export interface SimulatedDispatchFailedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "SimulatedDispatchFailed";
  idempotency_key: string | null;
  occurred_at: string;
  payload: SimulatedDispatchEndedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessGrantedEvent".
 */
export interface MedicalProfileAccessGrantedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "MedicalProfileAccessGranted";
  idempotency_key: string | null;
  occurred_at: string;
  payload: MedicalProfileAccessPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * Audit record: field *names* only, never profile values.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessPayload".
 */
export interface MedicalProfileAccessPayload {
  granted_fields: ("conditions" | "medications" | "allergies" | "emergency_contacts")[];
  incident_id: string;
  profile_ref: string;
  reason?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessDeniedEvent".
 */
export interface MedicalProfileAccessDeniedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "MedicalProfileAccessDenied";
  idempotency_key: string | null;
  occurred_at: string;
  payload: MedicalProfileAccessPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "HospitalPreAlertSimulatedEvent".
 */
export interface HospitalPreAlertSimulatedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "HospitalPreAlertSimulated";
  idempotency_key: string | null;
  occurred_at: string;
  payload: HospitalPreAlertSimulatedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "HospitalPreAlertSimulatedPayload".
 */
export interface HospitalPreAlertSimulatedPayload {
  capability_needed?: string | null;
  hospital_id: string;
  incident_id: string;
  outbox_key: string;
  simulated: true;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ModelAdapterDegradedEvent".
 */
export interface ModelAdapterDegradedEvent {
  actor: Actor;
  affects_planning: boolean;
  aggregate_id: string;
  aggregate_type: string;
  causation_id: string | null;
  correlation_id: string;
  event_id: string;
  event_type: "ModelAdapterDegraded";
  idempotency_key: string | null;
  occurred_at: string;
  payload: ModelAdapterDegradedPayload;
  schema_version: string;
  sequence: number;
  session_id: string;
  sim_time_s: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ModelAdapterDegradedPayload".
 */
export interface ModelAdapterDegradedPayload {
  adapter: "model_adapter" | "routing_provider" | "solver";
  cause: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactConfirmCommand".
 */
export interface FactConfirmCommand {
  count?: number | null;
  expected_session_id: string;
  reason_text: string;
  value?: FactValue | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodAccepted".
 */
export interface FloodAccepted {
  flood_id: string;
  sequence: number;
  version: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodEventCommand".
 */
export interface FloodEventCommand {
  closes_roads: boolean;
  effective_sim_time_s: number;
  expected_session_id: string;
  flood_id: string;
  geometry: Polygon;
  version: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "HealthResponse".
 */
export interface HealthResponse {
  degraded: string[];
  llm_provider: "template" | "gemini";
  mode: "simulation";
  routing_provider: "fixture" | "ors_directions";
  schema_version: string;
  status: "ok";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessCommand".
 */
export interface MedicalProfileAccessCommand {
  expected_session_id: string;
  operator_reason: string;
  profile_ref: string;
}
/**
 * Consent metadata only. Profile values live in a separate store and never in events.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileConsent".
 */
export interface MedicalProfileConsent {
  access_rule: AccessRule;
  consent: Consent;
  profile_ref: string;
  subject_ref: string;
  synthetic: true;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideCommand".
 */
export interface OverrideCommand {
  bridges_need_id?: string | null;
  expected_plan_id: string;
  expected_planning_sequence: number;
  expected_session_id: string;
  incident_id?: string | null;
  kind: OverrideKind;
  need_id?: string | null;
  reason_text: string;
  replaces_override_id?: string | null;
  revokes_override_id?: string | null;
  unit_id?: string | null;
  zone_id?: string | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRecorded".
 */
export interface OverrideRecorded {
  override_id: string;
  recompute: "computing";
  sequence: number;
  status: "active";
}
/**
 * RFC 9457 problem details with a stable machine ``code`` (0001).
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Problem".
 */
export interface Problem {
  code: string;
  conflicts?:
    | {
        [k: string]: unknown;
      }[]
    | null;
  current?: {
    [k: string]: unknown;
  } | null;
  detail?: string | null;
  errors?: ProblemFieldError[] | null;
  instance?: string | null;
  missing_flag_ids?: string[] | null;
  override_id?: string | null;
  reason?: string | null;
  status: number;
  title: string;
  type: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ProblemFieldError".
 */
export interface ProblemFieldError {
  message: string;
  pointer: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RecomputeAccepted".
 */
export interface RecomputeAccepted {
  planning_sequence: number;
  status: "computing";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RecomputeCommand".
 */
export interface RecomputeCommand {
  expected_session_id: string;
  reason: "operator_requested";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportAccepted".
 */
export interface ReportAccepted {
  escalated: boolean;
  incident_id: string | null;
  report_id: string;
  sequence: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportCommand".
 */
export interface ReportCommand {
  channel: "text_sim" | "structured_sim";
  expected_session_id: string;
  location: Point;
  location_source: "caller_stated" | "operator_entered" | "fixture";
  sim_time_s: number;
  text: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusAccepted".
 */
export interface UnitStatusAccepted {
  invalidated_assignment_ids: string[];
  sequence: number;
  status: UnitStatus;
  unit_id: string;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusCommand".
 */
export interface UnitStatusCommand {
  expected_session_id: string;
  position?: Point | null;
  sim_time_s: number;
  to_status: UnitStatus;
}
/**
 * Server confirms backlog delivery; clients enable commands only after this.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsCaughtUp".
 */
export interface WsCaughtUp {
  head_sequence: number;
  type: "caught_up";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsEvent".
 */
export interface WsEvent {
  event:
    | SessionStartedEvent
    | ReportReceivedEvent
    | TriageFactsExtractedEvent
    | TriageFactConfirmedEvent
    | IncidentCreatedEvent
    | IncidentAssessedEvent
    | IncidentCategoryChangedEvent
    | ReportLinkedToIncidentEvent
    | IncidentResolvedEvent
    | UnitStatusChangedEvent
    | PlanningTickCommittedEvent
    | FloodZoneUpdatedEvent
    | RoadClosureUpdatedEvent
    | FacilityCapacityUpdatedEvent
    | OverrideAcceptedEvent
    | OverrideInvalidatedEvent
    | OverrideRevokedEvent
    | PlanApprovedEvent
    | SimulatedDispatchSentEvent
    | UnitPositionObservedEvent
    | EscalatedToHumanEvent
    | DuplicateCandidateFlaggedEvent
    | PlanProposedEvent
    | PlanSupersededEvent
    | PlanRevalidatedEvent
    | PlanFailedEvent
    | ApprovalRejectedEvent
    | OverrideRejectedEvent
    | SimulatedDispatchQueuedEvent
    | SimulatedDispatchCancelledEvent
    | SimulatedDispatchFailedEvent
    | MedicalProfileAccessGrantedEvent
    | MedicalProfileAccessDeniedEvent
    | HospitalPreAlertSimulatedEvent
    | ModelAdapterDegradedEvent;
  type: "event";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsHeartbeat".
 */
export interface WsHeartbeat {
  head_sequence: number;
  type: "heartbeat";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsHello".
 */
export interface WsHello {
  head_sequence: number;
  schema_version: string;
  session_id: string;
  type: "hello";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsSnapshotRequired".
 */
export interface WsSnapshotRequired {
  session_id: string;
  type: "snapshot_required";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsSubscribe".
 */
export interface WsSubscribe {
  after_sequence: number;
  session_id: string;
  type: "subscribe";
}
