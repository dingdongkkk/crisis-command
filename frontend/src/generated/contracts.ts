/* Generated from contracts/schema/crisis-command.schema.json by npm run gen:contracts. Do not edit. */

export type RequiresActiveIncident = true;
export type RequiresCallerIsPatient = true;
export type RequiresOperatorReason = true;
export type Id = string;
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
export type ExpectedSessionId = string;
export type FactKey = string;
export type OutboxKeys = string[];
export type PlanId = string;
export type Sequence = number;
export type State = "approved" | "dispatched_simulated";
export type AffectsPlanning = boolean;
export type AggregateId = string;
export type AggregateType = string;
export type CausationId = string | null;
export type CorrelationId = string;
export type EventId = string;
export type EventType = "ApprovalRejected";
export type IdempotencyKey = string | null;
export type OccurredAt = string;
export type Code = string;
export type PlanId1 = string;
export type SchemaVersion = string;
export type Sequence1 = number;
export type SessionId = string;
export type SimTimeS = number;
export type AcknowledgedFlagIds = string[];
export type ExpectedPlanVersion = number;
export type ExpectedPlanningSequence = number;
export type ExpectedSessionId1 = string;
export type Note = string | null;
export type AssignmentId = string;
export type BridgesNeedId = string | null;
export type DestinationFacilityId = string | null;
export type EtaS = number;
export type IncidentId = string;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "LockReason".
 */
export type LockReason = "on_scene" | "transporting" | "near_arrival";
export type NeedId = string | null;
export type DistanceM = number | null;
export type DurationS = number | null;
export type FloodVersion = number;
/**
 * @minItems 2
 * @maxItems 2
 */
export type Coordinates = [unknown, unknown];
export type Type = "Point";
/**
 * @minItems 2
 */
export type Coordinates1 = [[unknown, unknown], [unknown, unknown], ...[unknown, unknown][]];
export type Type1 = "LineString";
export type Provider = "fixture" | "ors_directions";
export type RouteId = string;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RouteStatus".
 */
export type RouteStatus = "ok" | "unavailable" | "provider_error";
export type UnavailableReason = string | null;
export type Persons = number | null;
export type Code1 = string;
export type Reasons = ReasonFact[];
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "AssignmentRole".
 */
export type AssignmentRole = "primary" | "bridge";
export type SatisfiesNeed = boolean;
export type UnitId = string;
export type Delta = number | null;
export type Metric = "unmet_need" | "reserve_uncovered" | "already_assigned_same_incident" | "weighted_eta_s";
export type NeedId1 = string | null;
export type ZoneId = string | null;
export type CostOfTaking = CostOfTaking1[];
export type EtaS1 = number;
export type UnitId1 = string;
export type Granted = boolean;
export type GrantedAt = string;
export type Revocable = boolean;
export type Scope = ("conditions" | "medications" | "allergies" | "emergency_contacts")[];
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CountStatus".
 */
export type CountStatus = "known" | "approximate" | "unknown";
export type AvailableUnitIds = string[];
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
export type ZoneId1 = string;
export type AssignmentId1 = string;
export type IncidentId1 = string;
export type NeedId2 = string | null;
export type ExpectedSessionId2 = string;
export type ToStep = "T+0" | "T+2" | "T+5" | "T+10";
export type Appended = number;
export type HeadSequence = number;
export type SimTimeS1 = number;
export type ExpectedSessionId3 = string;
export type Fixture = "demo-bengaluru-v1";
export type Seed = number;
export type HeadSequence1 = number;
export type SessionId1 = string;
export type AssignmentId2 = string;
export type DesiredRevision = number;
export type UnitId2 = string;
export type EtaS2 = number | null;
export type IncidentId2 = string | null;
export type NeedId3 = string | null;
export type State1 = ("available" | "assigned" | "held") | null;
export type ZoneId2 = string | null;
export type UnitId3 = string;
export type NeedsUnmet = number;
export type UnitsAdded = number;
export type UnitsMoved = number;
export type UnitsReleased = number;
export type WeightedEtaDeltaS = number;
export type ZonesUncovered = number;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DispatchAction".
 */
export type DispatchAction = "assign" | "release" | "hospital_pre_alert";
export type AssignmentId3 = string;
export type DesiredRevision1 = number;
export type IncidentId3 = string | null;
export type OutboxKey = string;
export type PlanId2 = string;
export type SessionId2 = string;
export type Simulated = true;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DispatchState".
 */
export type DispatchState = "pending" | "sent" | "cancelled" | "failed";
export type UnitId4 = string | null;
export type AffectsPlanning1 = boolean;
export type AggregateId1 = string;
export type AggregateType1 = string;
export type CausationId1 = string | null;
export type CorrelationId1 = string;
export type EventId1 = string;
export type EventType1 = "DuplicateCandidateFlagged";
export type IdempotencyKey1 = string | null;
export type OccurredAt1 = string;
export type CandidateIncidentId = string;
export type Reasons1 = string[];
export type ReportId = string;
export type SchemaVersion1 = string;
export type Sequence2 = number;
export type SessionId3 = string;
export type SimTimeS2 = number;
export type ExpectedSessionId4 = string;
export type ReasonText = string;
export type Resolution = "linked" | "kept_separate";
export type AffectsPlanning2 = boolean;
export type AggregateId2 = string;
export type AggregateType2 = string;
export type CausationId2 = string | null;
export type CorrelationId2 = string;
export type EventId2 = string;
export type EventType2 = "EscalatedToHuman";
export type IdempotencyKey2 = string | null;
export type OccurredAt2 = string;
export type IncidentId4 = string;
/**
 * @minItems 1
 */
export type Reasons2 = [string, ...string[]];
export type SchemaVersion2 = string;
export type Sequence3 = number;
export type SessionId4 = string;
export type SimTimeS3 = number;
export type Escalated = boolean;
export type Reasons3 = string[];
export type SimTimeS4 = number | null;
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
export type AffectsPlanning3 = boolean;
export type AggregateId3 = string;
export type AggregateType3 = string;
export type CausationId3 = string | null;
export type CorrelationId3 = string;
export type EventId3 = string;
export type EventType3 = "SessionStarted";
export type IdempotencyKey3 = string | null;
export type OccurredAt3 = string;
export type Fixture1 = string;
export type AcceptedSequence = number | null;
export type BridgesNeedId1 = string | null;
export type ExpectedSessionId5 = string;
export type IncidentId5 = string | null;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideKind".
 */
export type OverrideKind = "pin" | "forbid" | "hold_unit" | "approve_bls_bridge" | "downgrade_need" | "revoke";
export type NeedId4 = string | null;
export type OverrideId = string;
export type ReasonText1 = string;
export type ReplacesOverrideId = string | null;
export type RevokesOverrideId = string | null;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideStatus".
 */
export type OverrideStatus = "active" | "rejected" | "invalidated" | "revoked";
export type UnitId5 = string | null;
export type ZoneId3 = string | null;
export type ActiveOverrides = Override[];
export type Assignments = Assignment[];
export type BasedOnPlanningSequence = number;
export type Coverage1 = Coverage[];
export type CreatedAt = string;
export type CreatedSimTimeS = number;
export type Added = DiffRow[];
export type AgainstPlanId = string | null;
export type Changed = DiffRow[];
export type NewlyUnmet = string[];
export type Released = DiffRow[];
export type UnchangedCount = number;
export type AllocationId = string;
export type FacilityId = string;
export type FreeAfterPersons = number;
export type IncidentId6 = string;
export type NeedId5 = string;
export type Persons1 = number;
export type FacilityAllocations = FacilityAllocation[];
export type Code2 = string;
export type FlagId = string;
export type IncidentId7 = string | null;
export type Message = string;
export type NeedId6 = string | null;
export type OverrideId1 = string | null;
export type RequiresAck = boolean;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FlagSeverity".
 */
export type FlagSeverity = "critical" | "warning" | "info";
export type SinceSimTimeS = number | null;
export type ZoneId4 = string | null;
export type Flags = PolicyFlag[];
export type PlanId3 = string;
export type PolicyVersion = string;
export type SchemaVersion3 = string;
export type SessionId5 = string;
export type Delta1 = number | null;
export type Metric1 = "weighted_eta_s" | "reserve_uncovered" | "unmet_need";
export type NeedId7 = string | null;
export type OverrideId2 = string | null;
export type ZoneId5 = string | null;
export type SoftConsequences = SoftConsequence[];
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ObjectiveTier".
 */
export type ObjectiveTier =
  "unmet_critical" | "unmet_high" | "unmet_medium" | "unmet_low" | "waiting_cost" | "operating_cost";
export type CompletedTiers = ObjectiveTier[];
export type Engine = "ortools_cp_sat" | "greedy_fallback";
export type LexicographicComplete = boolean;
/**
 * @minItems 6
 * @maxItems 6
 */
export type ObjectiveVector = [number, number, number, number, number, number];
export type Seed1 = number;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SolverStatus".
 */
export type SolverStatus = "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "UNKNOWN" | "MODEL_INVALID" | "FALLBACK";
export type TieBreakComplete = boolean;
export type WallTimeMs = number;
export type Workers = number;
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
export type SupersedesApprovedPlanId = string | null;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "NeedBasis".
 */
export type NeedBasis = "confirmed" | "provisional_unknown";
/**
 * @maxItems 3
 */
export type BridgeCandidates =
  [] | [BridgeCandidate] | [BridgeCandidate, BridgeCandidate] | [BridgeCandidate, BridgeCandidate, BridgeCandidate];
export type IncidentId8 = string;
export type NeedId8 = string;
export type QuantityUnmet = number;
export type Reasons4 = ReasonFact[];
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
export type WaitingS = number;
export type UnmetNeeds = UnmetNeed[];
export type Version = number;
export type AsOfSequence = number;
export type Capabilities = ("emergency" | "cardiac" | "trauma" | "burns" | "paediatric")[];
export type DisplayName = string;
export type EdBedsAvailable = number;
export type FacilityId1 = string;
export type Kind = "hospital";
export type CapacityPersons = number;
export type DisplayName1 = string;
export type FacilityId2 = string;
export type Kind1 = "shelter";
export type OccupiedPersons = number;
export type Facilities = (Hospital | Shelter)[];
export type ClosesRoads = boolean;
export type EffectiveSimTimeS = number;
export type FloodId = string;
/**
 * @minItems 1
 */
export type Coordinates2 = [[unknown, unknown][], ...[unknown, unknown][][]];
export type Type2 = "Polygon";
export type Source = "synthetic_progression" | "operator_entered";
export type Version1 = number;
export type Flood = FloodZone[];
export type HistoricalPlans = Plan[] | null;
export type AssumedFacts = string[];
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCategory".
 */
export type IncidentCategory = "emergency" | "non_emergency_assist" | "information_request";
export type CreatedSimTimeS1 = number;
export type DuplicateCandidateOf = string[];
export type IncidentId9 = string;
export type Kind2 = string;
export type NeedId9 = string;
export type Quantity = number;
export type Reasons5 = ReasonFact[];
export type Needs = Need[];
export type ReportIds = string[];
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentStatus".
 */
export type IncidentStatus = "active" | "resolved" | "merged_duplicate";
export type Incidents = Incident[];
export type Outbox = DispatchCommand[];
export type PlanningSequence = number;
export type AlsOnBls = number;
export type Reassignment = number;
export type ReserveShortfall = number;
export type TravelCapS = number;
export type WaitingCapS = number;
export type DemandQuanta = number;
export type NeedRecords = number;
export type ReservePairs = number;
export type Units = number;
export type MaxDebounceMs = number;
export type NearArrivalLockS = number;
export type ObjectiveTiers = ObjectiveTier[];
export type PlanningTickS = number;
export type PolicyVersion1 = string;
export type SolverBudgetMs = number;
export type Channel = "text_sim" | "structured_sim";
export type LinkedIncidentId = string | null;
export type LocationSource = "caller_stated" | "operator_entered" | "fixture";
export type ReceivedAt = string;
export type ReceivedSimTimeS = number;
export type ReportId1 = string;
export type LengthChars = number;
export type ReportId2 = string | null;
export type Store = "report_text";
export type TextSha256 = string;
export type Reports = Report[];
export type CoverageEtaS = number;
export type RequiredTypes = UnitType[];
export type ZoneId6 = string;
export type ReserveZones = ReserveZone[];
export type SchemaVersion4 = string;
export type SessionId6 = string;
export type SimTimeS5 = number;
export type ApplicableFacts = string[];
export type CoercionReason = string | null;
export type ConfirmedByOperator = boolean;
export type Conflict = boolean | null;
export type Value = number | null;
export type End = number;
export type ReportId3 = string;
export type Start = number;
export type Evidence = EvidenceSpan[];
export type Key = string;
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactSource".
 */
export type FactSource = "caller_structured" | "rule_adapter" | "model_adapter" | "operator" | "medical_profile";
export type UpdatedSimTimeS = number;
export type Facts = TriageFact[];
export type IncidentId10 = string;
export type PolicyVersion2 = string;
export type AskedSimTimeS = number;
export type FactKey1 = string;
export type QuestionsAsked = QuestionAsked[];
export type TriageFacts = TriageFacts1[];
export type CapacityPersons1 = number;
export type DesiredRevision2 = number | null;
export type DisplayName2 = string;
export type HomeZoneId = string;
export type PositionSimTimeS = number;
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
export type UnitId6 = string;
export type Units1 = Unit[];
export type Seed2 = number;
export type SchemaVersion5 = string;
export type Sequence4 = number;
export type SessionId7 = string;
export type SimTimeS6 = number;
export type AffectsPlanning4 = boolean;
export type AggregateId4 = string;
export type AggregateType4 = string;
export type CausationId4 = string | null;
export type CorrelationId4 = string;
export type EventId4 = string;
export type EventType4 = "ReportReceived";
export type IdempotencyKey4 = string | null;
export type OccurredAt4 = string;
export type SchemaVersion6 = string;
export type Sequence5 = number;
export type SessionId8 = string;
export type SimTimeS7 = number;
export type AffectsPlanning5 = boolean;
export type AggregateId5 = string;
export type AggregateType5 = string;
export type CausationId5 = string | null;
export type CorrelationId5 = string;
export type EventId5 = string;
export type EventType5 = "TriageFactsExtracted";
export type IdempotencyKey5 = string | null;
export type OccurredAt5 = string;
export type SchemaVersion7 = string;
export type Sequence6 = number;
export type SessionId9 = string;
export type SimTimeS8 = number;
export type AffectsPlanning6 = boolean;
export type AggregateId6 = string;
export type AggregateType6 = string;
export type CausationId6 = string | null;
export type CorrelationId6 = string;
export type EventId6 = string;
export type EventType6 = "TriageFactConfirmed";
export type IdempotencyKey6 = string | null;
export type OccurredAt6 = string;
export type IncidentId11 = string;
export type SchemaVersion8 = string;
export type Sequence7 = number;
export type SessionId10 = string;
export type SimTimeS9 = number;
export type AffectsPlanning7 = boolean;
export type AggregateId7 = string;
export type AggregateType7 = string;
export type CausationId7 = string | null;
export type CorrelationId7 = string;
export type EventId7 = string;
export type EventType7 = "IncidentCreated";
export type IdempotencyKey7 = string | null;
export type OccurredAt7 = string;
export type SchemaVersion9 = string;
export type Sequence8 = number;
export type SessionId11 = string;
export type SimTimeS10 = number;
export type AffectsPlanning8 = boolean;
export type AggregateId8 = string;
export type AggregateType8 = string;
export type CausationId8 = string | null;
export type CorrelationId8 = string;
export type EventId8 = string;
export type EventType8 = "IncidentAssessed";
export type IdempotencyKey8 = string | null;
export type OccurredAt8 = string;
export type SchemaVersion10 = string;
export type Sequence9 = number;
export type SessionId12 = string;
export type SimTimeS11 = number;
export type AffectsPlanning9 = boolean;
export type AggregateId9 = string;
export type AggregateType9 = string;
export type CausationId9 = string | null;
export type CorrelationId9 = string;
export type EventId9 = string;
export type EventType9 = "IncidentCategoryChanged";
export type IdempotencyKey9 = string | null;
export type OccurredAt9 = string;
export type Reason = string;
export type TriggeringFactKeys = string[];
export type SchemaVersion11 = string;
export type Sequence10 = number;
export type SessionId13 = string;
export type SimTimeS12 = number;
export type AffectsPlanning10 = boolean;
export type AggregateId10 = string;
export type AggregateType10 = string;
export type CausationId10 = string | null;
export type CorrelationId10 = string;
export type EventId10 = string;
export type EventType10 = "ReportLinkedToIncident";
export type IdempotencyKey10 = string | null;
export type OccurredAt10 = string;
export type IncidentId12 = string;
export type ReportId4 = string;
export type Resolution1 = "linked" | "kept_separate";
export type SchemaVersion12 = string;
export type Sequence11 = number;
export type SessionId14 = string;
export type SimTimeS13 = number;
export type AffectsPlanning11 = boolean;
export type AggregateId11 = string;
export type AggregateType11 = string;
export type CausationId11 = string | null;
export type CorrelationId11 = string;
export type EventId11 = string;
export type EventType11 = "IncidentResolved";
export type IdempotencyKey11 = string | null;
export type OccurredAt11 = string;
export type IncidentId13 = string;
export type InvalidatesAssignmentIds = string[];
export type SchemaVersion13 = string;
export type Sequence12 = number;
export type SessionId15 = string;
export type SimTimeS14 = number;
export type AffectsPlanning12 = boolean;
export type AggregateId12 = string;
export type AggregateType12 = string;
export type CausationId12 = string | null;
export type CorrelationId12 = string;
export type EventId12 = string;
export type EventType12 = "UnitStatusChanged";
export type IdempotencyKey12 = string | null;
export type OccurredAt12 = string;
export type InvalidatesAssignmentIds1 = string[];
export type SchemaVersion14 = string;
export type Sequence13 = number;
export type SessionId16 = string;
export type SimTimeS15 = number;
export type AffectsPlanning13 = boolean;
export type AggregateId13 = string;
export type AggregateType13 = string;
export type CausationId13 = string | null;
export type CorrelationId13 = string;
export type EventId13 = string;
export type EventType13 = "PlanningTickCommitted";
export type IdempotencyKey13 = string | null;
export type OccurredAt13 = string;
export type TickSimTimeS = number;
export type Lock = ("on_scene" | "transporting" | "near_arrival") | null;
export type RemainingRouteS = number | null;
export type UnitId7 = string;
export type Units2 = UnitPlanningState[];
export type SchemaVersion15 = string;
export type Sequence14 = number;
export type SessionId17 = string;
export type SimTimeS16 = number;
export type AffectsPlanning14 = boolean;
export type AggregateId14 = string;
export type AggregateType14 = string;
export type CausationId14 = string | null;
export type CorrelationId14 = string;
export type EventId14 = string;
export type EventType14 = "FloodZoneUpdated";
export type IdempotencyKey14 = string | null;
export type OccurredAt14 = string;
export type SchemaVersion16 = string;
export type Sequence15 = number;
export type SessionId18 = string;
export type SimTimeS17 = number;
export type AffectsPlanning15 = boolean;
export type AggregateId15 = string;
export type AggregateType15 = string;
export type CausationId15 = string | null;
export type CorrelationId15 = string;
export type EventId15 = string;
export type EventType15 = "RoadClosureUpdated";
export type IdempotencyKey15 = string | null;
export type OccurredAt15 = string;
export type Closed = boolean;
export type ClosureId = string;
export type Version2 = number;
export type SchemaVersion17 = string;
export type Sequence16 = number;
export type SessionId19 = string;
export type SimTimeS18 = number;
export type AffectsPlanning16 = boolean;
export type AggregateId16 = string;
export type AggregateType16 = string;
export type CausationId16 = string | null;
export type CorrelationId16 = string;
export type EventId16 = string;
export type EventType16 = "FacilityCapacityUpdated";
export type IdempotencyKey16 = string | null;
export type OccurredAt16 = string;
export type EdBedsAvailable1 = number | null;
export type FacilityId3 = string;
export type OccupiedPersons1 = number | null;
export type SchemaVersion18 = string;
export type Sequence17 = number;
export type SessionId20 = string;
export type SimTimeS19 = number;
export type AffectsPlanning17 = boolean;
export type AggregateId17 = string;
export type AggregateType17 = string;
export type CausationId17 = string | null;
export type CorrelationId17 = string;
export type EventId17 = string;
export type EventType17 = "OverrideAccepted";
export type IdempotencyKey17 = string | null;
export type OccurredAt17 = string;
export type SchemaVersion19 = string;
export type Sequence18 = number;
export type SessionId21 = string;
export type SimTimeS20 = number;
export type AffectsPlanning18 = boolean;
export type AggregateId18 = string;
export type AggregateType18 = string;
export type CausationId18 = string | null;
export type CorrelationId18 = string;
export type EventId18 = string;
export type EventType18 = "OverrideInvalidated";
export type IdempotencyKey18 = string | null;
export type OccurredAt18 = string;
export type OverrideId3 = string;
export type Reason1 = string;
export type SchemaVersion20 = string;
export type Sequence19 = number;
export type SessionId22 = string;
export type SimTimeS21 = number;
export type AffectsPlanning19 = boolean;
export type AggregateId19 = string;
export type AggregateType19 = string;
export type CausationId19 = string | null;
export type CorrelationId19 = string;
export type EventId19 = string;
export type EventType19 = "OverrideRevoked";
export type IdempotencyKey19 = string | null;
export type OccurredAt19 = string;
export type SchemaVersion21 = string;
export type Sequence20 = number;
export type SessionId23 = string;
export type SimTimeS22 = number;
export type AffectsPlanning20 = boolean;
export type AggregateId20 = string;
export type AggregateType20 = string;
export type CausationId20 = string | null;
export type CorrelationId20 = string;
export type EventId20 = string;
export type EventType20 = "PlanApproved";
export type IdempotencyKey20 = string | null;
export type OccurredAt20 = string;
export type AcknowledgedFlagIds1 = string[];
export type BasedOnPlanningSequence1 = number;
export type DesiredAssignments = DesiredAssignment[];
export type NotePresent = boolean | null;
export type OutboxKeys1 = string[];
export type PlanId4 = string;
export type Version3 = number;
export type SchemaVersion22 = string;
export type Sequence21 = number;
export type SessionId24 = string;
export type SimTimeS23 = number;
export type AffectsPlanning21 = boolean;
export type AggregateId21 = string;
export type AggregateType21 = string;
export type CausationId21 = string | null;
export type CorrelationId21 = string;
export type EventId21 = string;
export type EventType21 = "SimulatedDispatchSent";
export type IdempotencyKey21 = string | null;
export type OccurredAt21 = string;
export type AssignmentId4 = string;
export type OutboxKey1 = string;
export type Simulated1 = true;
export type UnitId8 = string | null;
export type SchemaVersion23 = string;
export type Sequence22 = number;
export type SessionId25 = string;
export type SimTimeS24 = number;
export type AffectsPlanning22 = boolean;
export type AggregateId22 = string;
export type AggregateType22 = string;
export type CausationId22 = string | null;
export type CorrelationId22 = string;
export type EventId22 = string;
export type EventType22 = "UnitPositionObserved";
export type IdempotencyKey22 = string | null;
export type OccurredAt22 = string;
export type ObservedSimTimeS = number;
export type UnitId9 = string;
export type SchemaVersion24 = string;
export type Sequence23 = number;
export type SessionId26 = string;
export type SimTimeS25 = number;
export type AffectsPlanning23 = boolean;
export type AggregateId23 = string;
export type AggregateType23 = string;
export type CausationId23 = string | null;
export type CorrelationId23 = string;
export type EventId23 = string;
export type EventType23 = "PlanProposed";
export type IdempotencyKey23 = string | null;
export type OccurredAt23 = string;
export type SchemaVersion25 = string;
export type Sequence24 = number;
export type SessionId27 = string;
export type SimTimeS26 = number;
export type AffectsPlanning24 = boolean;
export type AggregateId24 = string;
export type AggregateType24 = string;
export type CausationId24 = string | null;
export type CorrelationId24 = string;
export type EventId24 = string;
export type EventType24 = "PlanSuperseded";
export type IdempotencyKey24 = string | null;
export type OccurredAt24 = string;
export type PlanId5 = string;
export type Reason2 = string;
export type SupersededByPlanId = string | null;
export type SchemaVersion26 = string;
export type Sequence25 = number;
export type SessionId28 = string;
export type SimTimeS27 = number;
export type AffectsPlanning25 = boolean;
export type AggregateId25 = string;
export type AggregateType25 = string;
export type CausationId25 = string | null;
export type CorrelationId25 = string;
export type EventId25 = string;
export type EventType25 = "PlanRevalidated";
export type IdempotencyKey25 = string | null;
export type OccurredAt25 = string;
export type CheckedPlanningSequence = number;
export type CheckedSimTimeS = number;
export type PlanId6 = string;
export type SchemaVersion27 = string;
export type Sequence26 = number;
export type SessionId29 = string;
export type SimTimeS28 = number;
export type AffectsPlanning26 = boolean;
export type AggregateId26 = string;
export type AggregateType26 = string;
export type CausationId26 = string | null;
export type CorrelationId26 = string;
export type EventId26 = string;
export type EventType26 = "PlanFailed";
export type IdempotencyKey26 = string | null;
export type OccurredAt26 = string;
export type BasedOnPlanningSequence2 = number;
export type PlanId7 = string;
export type Reasons6 = string[];
export type SchemaVersion28 = string;
export type Sequence27 = number;
export type SessionId30 = string;
export type SimTimeS29 = number;
export type AffectsPlanning27 = boolean;
export type AggregateId27 = string;
export type AggregateType27 = string;
export type CausationId27 = string | null;
export type CorrelationId27 = string;
export type EventId27 = string;
export type EventType27 = "OverrideRejected";
export type IdempotencyKey27 = string | null;
export type OccurredAt27 = string;
export type BridgesNeedId2 = string | null;
/**
 * @minItems 1
 */
export type Conflicts = [OverrideConflict, ...OverrideConflict[]];
export type Code3 = string;
export type Detail = string;
export type OverrideId4 = string | null;
export type UnitId10 = string | null;
export type IncidentId14 = string | null;
export type NeedId10 = string | null;
export type OverrideId5 = string;
export type UnitId11 = string | null;
export type SchemaVersion29 = string;
export type Sequence28 = number;
export type SessionId31 = string;
export type SimTimeS30 = number;
export type AffectsPlanning28 = boolean;
export type AggregateId28 = string;
export type AggregateType28 = string;
export type CausationId28 = string | null;
export type CorrelationId28 = string;
export type EventId28 = string;
export type EventType28 = "SimulatedDispatchQueued";
export type IdempotencyKey28 = string | null;
export type OccurredAt28 = string;
export type SchemaVersion30 = string;
export type Sequence29 = number;
export type SessionId32 = string;
export type SimTimeS31 = number;
export type AffectsPlanning29 = boolean;
export type AggregateId29 = string;
export type AggregateType29 = string;
export type CausationId29 = string | null;
export type CorrelationId29 = string;
export type EventId29 = string;
export type EventType29 = "SimulatedDispatchCancelled";
export type IdempotencyKey29 = string | null;
export type OccurredAt29 = string;
export type Attempts = number | null;
export type OutboxKey2 = string;
export type Reason3 = string;
export type SchemaVersion31 = string;
export type Sequence30 = number;
export type SessionId33 = string;
export type SimTimeS32 = number;
export type AffectsPlanning30 = boolean;
export type AggregateId30 = string;
export type AggregateType30 = string;
export type CausationId30 = string | null;
export type CorrelationId30 = string;
export type EventId30 = string;
export type EventType30 = "SimulatedDispatchFailed";
export type IdempotencyKey30 = string | null;
export type OccurredAt30 = string;
export type SchemaVersion32 = string;
export type Sequence31 = number;
export type SessionId34 = string;
export type SimTimeS33 = number;
export type AffectsPlanning31 = boolean;
export type AggregateId31 = string;
export type AggregateType31 = string;
export type CausationId31 = string | null;
export type CorrelationId31 = string;
export type EventId31 = string;
export type EventType31 = "MedicalProfileAccessGranted";
export type IdempotencyKey31 = string | null;
export type OccurredAt31 = string;
export type GrantedFields = ("conditions" | "medications" | "allergies" | "emergency_contacts")[];
export type IncidentId15 = string;
export type ProfileRef = string;
export type Reason4 = string | null;
export type SchemaVersion33 = string;
export type Sequence32 = number;
export type SessionId35 = string;
export type SimTimeS34 = number;
export type AffectsPlanning32 = boolean;
export type AggregateId32 = string;
export type AggregateType32 = string;
export type CausationId32 = string | null;
export type CorrelationId32 = string;
export type EventId32 = string;
export type EventType32 = "MedicalProfileAccessDenied";
export type IdempotencyKey32 = string | null;
export type OccurredAt32 = string;
export type SchemaVersion34 = string;
export type Sequence33 = number;
export type SessionId36 = string;
export type SimTimeS35 = number;
export type AffectsPlanning33 = boolean;
export type AggregateId33 = string;
export type AggregateType33 = string;
export type CausationId33 = string | null;
export type CorrelationId33 = string;
export type EventId33 = string;
export type EventType33 = "HospitalPreAlertSimulated";
export type IdempotencyKey33 = string | null;
export type OccurredAt33 = string;
export type CapabilityNeeded = string | null;
export type HospitalId = string;
export type IncidentId16 = string;
export type OutboxKey3 = string;
export type Simulated2 = true;
export type SchemaVersion35 = string;
export type Sequence34 = number;
export type SessionId37 = string;
export type SimTimeS36 = number;
export type AffectsPlanning34 = boolean;
export type AggregateId34 = string;
export type AggregateType34 = string;
export type CausationId34 = string | null;
export type CorrelationId34 = string;
export type EventId34 = string;
export type EventType34 = "ModelAdapterDegraded";
export type IdempotencyKey34 = string | null;
export type OccurredAt34 = string;
export type Adapter = "model_adapter" | "routing_provider" | "solver";
export type Cause = string;
export type SchemaVersion36 = string;
export type Sequence35 = number;
export type SessionId38 = string;
export type SimTimeS37 = number;
export type Count = number | null;
export type ExpectedSessionId6 = string;
export type ReasonText2 = string;
export type FloodId1 = string;
export type Sequence36 = number;
export type Version4 = number;
export type ClosesRoads1 = boolean;
export type EffectiveSimTimeS1 = number;
export type ExpectedSessionId7 = string;
export type FloodId2 = string;
export type Version5 = number;
export type Degraded = string[];
export type LlmProvider = "template" | "gemini";
export type Mode = "simulation";
export type RoutingProvider = "fixture" | "ors_directions";
export type SchemaVersion37 = string;
export type Status = "ok";
export type ExpectedSessionId8 = string;
export type OperatorReason = string;
export type ProfileRef1 = string;
export type ProfileRef2 = string;
export type SubjectRef = string;
export type Synthetic = true;
export type BridgesNeedId3 = string | null;
export type ExpectedPlanId = string;
export type ExpectedPlanningSequence1 = number;
export type ExpectedSessionId9 = string;
export type IncidentId17 = string | null;
export type NeedId11 = string | null;
export type ReasonText3 = string;
export type ReplacesOverrideId1 = string | null;
export type RevokesOverrideId1 = string | null;
export type UnitId12 = string | null;
export type ZoneId7 = string | null;
export type OverrideId6 = string;
export type Recompute = "computing";
export type Sequence37 = number;
export type Status1 = "active";
export type Code4 = string;
export type Conflicts1 =
  | {
      [k: string]: unknown;
    }[]
  | null;
export type Current = {
  [k: string]: unknown;
} | null;
export type Detail1 = string | null;
export type Errors = ProblemFieldError[] | null;
export type Message1 = string;
export type Pointer = string;
export type Instance = string | null;
export type MissingFlagIds = string[] | null;
export type OverrideId7 = string | null;
export type Reason5 = string | null;
export type Status2 = number;
export type Title = string;
export type Type3 = string;
export type PlanningSequence1 = number;
export type Status3 = "computing";
export type ExpectedSessionId10 = string;
export type Reason6 = "operator_requested";
export type Escalated1 = boolean;
export type IncidentId18 = string | null;
export type ReportId5 = string;
export type Sequence38 = number;
export type Channel1 = "text_sim" | "structured_sim";
export type ExpectedSessionId11 = string;
export type LocationSource1 = "caller_stated" | "operator_entered" | "fixture";
export type SimTimeS38 = number;
export type Text = string;
export type InvalidatedAssignmentIds = string[];
export type Sequence39 = number;
export type UnitId13 = string;
export type ExpectedSessionId12 = string;
export type SimTimeS39 = number;
export type HeadSequence2 = number;
export type Type4 = "caught_up";
export type Event =
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
export type Type5 = "event";
export type HeadSequence3 = number;
export type Type6 = "heartbeat";
export type HeadSequence4 = number;
export type SchemaVersion38 = string;
export type SessionId39 = string;
export type Type7 = "hello";
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsServerMessage".
 */
export type WsServerMessage = WsHello | WsEvent | WsHeartbeat | WsSnapshotRequired | WsCaughtUp;
export type SessionId40 = string;
export type Type8 = "snapshot_required";
export type AfterSequence = number;
export type SessionId41 = string;
export type Type9 = "subscribe";

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
  requires_active_incident: RequiresActiveIncident;
  requires_caller_is_patient: RequiresCallerIsPatient;
  requires_operator_reason: RequiresOperatorReason;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Actor".
 */
export interface Actor {
  id: Id;
  kind: ActorKind;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "AnswerCommand".
 */
export interface AnswerCommand {
  answer: FactValue;
  expected_session_id: ExpectedSessionId;
  fact_key: FactKey;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApprovalAccepted".
 */
export interface ApprovalAccepted {
  outbox_keys: OutboxKeys;
  plan_id: PlanId;
  sequence: Sequence;
  state: State;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApprovalRejectedEvent".
 */
export interface ApprovalRejectedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning;
  aggregate_id: AggregateId;
  aggregate_type: AggregateType;
  causation_id: CausationId;
  correlation_id: CorrelationId;
  event_id: EventId;
  event_type: EventType;
  idempotency_key: IdempotencyKey;
  occurred_at: OccurredAt;
  payload: ApprovalRejectedPayload;
  schema_version: SchemaVersion;
  sequence: Sequence1;
  session_id: SessionId;
  sim_time_s: SimTimeS;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApprovalRejectedPayload".
 */
export interface ApprovalRejectedPayload {
  code: Code;
  plan_id: PlanId1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ApproveCommand".
 */
export interface ApproveCommand {
  acknowledged_flag_ids: AcknowledgedFlagIds;
  expected_plan_version: ExpectedPlanVersion;
  expected_planning_sequence: ExpectedPlanningSequence;
  expected_session_id: ExpectedSessionId1;
  note?: Note;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Assignment".
 */
export interface Assignment {
  assignment_id: AssignmentId;
  bridges_need_id?: BridgesNeedId;
  destination_facility_id?: DestinationFacilityId;
  eta_s: EtaS;
  incident_id: IncidentId;
  locked: LockReason | null;
  need_id?: NeedId;
  onward_route?: Route | null;
  persons?: Persons;
  reasons: Reasons;
  role: AssignmentRole;
  route: Route;
  satisfies_need: SatisfiesNeed;
  unit_id: UnitId;
}
/**
 * A recorded route result. Unavailable routes never carry an estimate (0003 H5).
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Route".
 */
export interface Route {
  distance_m: DistanceM;
  duration_s: DurationS;
  flood_version: FloodVersion;
  from: Point;
  geometry: LineString | null;
  provider: Provider;
  route_id: RouteId;
  route_status: RouteStatus;
  to: Point;
  unavailable_reason?: UnavailableReason;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Point".
 */
export interface Point {
  coordinates: Coordinates;
  type: Type;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "LineString".
 */
export interface LineString {
  coordinates: Coordinates1;
  type: Type1;
}
/**
 * Typed evidence for explanations; templates and models may only restate these.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReasonFact".
 */
export interface ReasonFact {
  code: Code1;
  params?: Params;
}
export interface Params {
  [k: string]: string | number | boolean | string[] | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "BridgeCandidate".
 */
export interface BridgeCandidate {
  cost_of_taking: CostOfTaking;
  eta_s: EtaS1;
  unit_id: UnitId1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CostOfTaking".
 */
export interface CostOfTaking1 {
  delta?: Delta;
  metric: Metric;
  need_id?: NeedId1;
  zone_id?: ZoneId;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Consent".
 */
export interface Consent {
  granted: Granted;
  granted_at: GrantedAt;
  revocable: Revocable;
  scope: Scope;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Coverage".
 */
export interface Coverage {
  available_unit_ids: AvailableUnitIds;
  resource_type: UnitType;
  status: CoverageStatus;
  zone_id: ZoneId1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "CurrentTask".
 */
export interface CurrentTask {
  assignment_id: AssignmentId1;
  incident_id: IncidentId1;
  need_id?: NeedId2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoAdvanceCommand".
 */
export interface DemoAdvanceCommand {
  expected_session_id: ExpectedSessionId2;
  to_step: ToStep;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoAdvanceResult".
 */
export interface DemoAdvanceResult {
  appended: Appended;
  head_sequence: HeadSequence;
  sim_time_s: SimTimeS1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoResetCommand".
 */
export interface DemoResetCommand {
  expected_session_id: ExpectedSessionId3;
  fixture: Fixture;
  seed: Seed;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DemoResetResult".
 */
export interface DemoResetResult {
  head_sequence: HeadSequence1;
  session_id: SessionId1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DesiredAssignment".
 */
export interface DesiredAssignment {
  assignment_id: AssignmentId2;
  desired_revision: DesiredRevision;
  unit_id: UnitId2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DiffEndpoint".
 */
export interface DiffEndpoint {
  eta_s?: EtaS2;
  incident_id?: IncidentId2;
  need_id?: NeedId3;
  state?: State1;
  zone_id?: ZoneId2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DiffRow".
 */
export interface DiffRow {
  from: DiffEndpoint;
  reason?: ReasonFact | null;
  to?: DiffEndpoint | null;
  unit_id: UnitId3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DiffTotals".
 */
export interface DiffTotals {
  needs_unmet: NeedsUnmet;
  units_added: UnitsAdded;
  units_moved: UnitsMoved;
  units_released: UnitsReleased;
  weighted_eta_delta_s: WeightedEtaDeltaS;
  zones_uncovered: ZonesUncovered;
}
/**
 * Simulated outbox command. ``simulated`` is always true; no real transport exists.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DispatchCommand".
 */
export interface DispatchCommand {
  action: DispatchAction;
  assignment_id: AssignmentId3;
  desired_revision: DesiredRevision1;
  incident_id?: IncidentId3;
  outbox_key: OutboxKey;
  plan_id: PlanId2;
  session_id: SessionId2;
  simulated: Simulated;
  state: DispatchState;
  unit_id?: UnitId4;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DuplicateCandidateFlaggedEvent".
 */
export interface DuplicateCandidateFlaggedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning1;
  aggregate_id: AggregateId1;
  aggregate_type: AggregateType1;
  causation_id: CausationId1;
  correlation_id: CorrelationId1;
  event_id: EventId1;
  event_type: EventType1;
  idempotency_key: IdempotencyKey1;
  occurred_at: OccurredAt1;
  payload: DuplicateCandidateFlaggedPayload;
  schema_version: SchemaVersion1;
  sequence: Sequence2;
  session_id: SessionId3;
  sim_time_s: SimTimeS2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DuplicateCandidateFlaggedPayload".
 */
export interface DuplicateCandidateFlaggedPayload {
  candidate_incident_id: CandidateIncidentId;
  reasons: Reasons1;
  report_id: ReportId;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "DuplicateResolveCommand".
 */
export interface DuplicateResolveCommand {
  expected_session_id: ExpectedSessionId4;
  reason_text: ReasonText;
  resolution: Resolution;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EscalatedToHumanEvent".
 */
export interface EscalatedToHumanEvent {
  actor: Actor;
  affects_planning: AffectsPlanning2;
  aggregate_id: AggregateId2;
  aggregate_type: AggregateType2;
  causation_id: CausationId2;
  correlation_id: CorrelationId2;
  event_id: EventId2;
  event_type: EventType2;
  idempotency_key: IdempotencyKey2;
  occurred_at: OccurredAt2;
  payload: EscalatedToHumanPayload;
  schema_version: SchemaVersion2;
  sequence: Sequence3;
  session_id: SessionId4;
  sim_time_s: SimTimeS3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EscalatedToHumanPayload".
 */
export interface EscalatedToHumanPayload {
  incident_id: IncidentId4;
  reasons: Reasons2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Escalation".
 */
export interface Escalation {
  escalated: Escalated;
  reasons: Reasons3;
  sim_time_s?: SimTimeS4;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SessionStartedEvent".
 */
export interface SessionStartedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning3;
  aggregate_id: AggregateId3;
  aggregate_type: AggregateType3;
  causation_id: CausationId3;
  correlation_id: CorrelationId3;
  event_id: EventId3;
  event_type: EventType3;
  idempotency_key: IdempotencyKey3;
  occurred_at: OccurredAt3;
  payload: SessionStartedPayload;
  schema_version: SchemaVersion5;
  sequence: Sequence4;
  session_id: SessionId7;
  sim_time_s: SimTimeS6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SessionStartedPayload".
 */
export interface SessionStartedPayload {
  fixture: Fixture1;
  initial_state: StateSnapshot;
  seed: Seed2;
}
/**
 * ``GET /state`` body; also the checkpoint embedded in ``SessionStarted``.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "StateSnapshot".
 */
export interface StateSnapshot {
  active_overrides: ActiveOverrides;
  approved_plan: Plan | null;
  as_of_sequence: AsOfSequence;
  current_proposal: Plan | null;
  facilities: Facilities;
  flood: Flood;
  historical_plans?: HistoricalPlans;
  incidents: Incidents;
  outbox: Outbox;
  planning_sequence: PlanningSequence;
  policy: Policy;
  reports: Reports;
  reserve_zones: ReserveZones;
  schema_version: SchemaVersion4;
  session_id: SessionId6;
  sim_time_s: SimTimeS5;
  triage_facts: TriageFacts;
  units: Units1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Override".
 */
export interface Override {
  accepted_sequence?: AcceptedSequence;
  bridges_need_id?: BridgesNeedId1;
  created_by: Actor;
  expected_session_id: ExpectedSessionId5;
  incident_id?: IncidentId5;
  kind: OverrideKind;
  need_id?: NeedId4;
  override_id: OverrideId;
  reason_text: ReasonText1;
  replaces_override_id?: ReplacesOverrideId;
  revokes_override_id?: RevokesOverrideId;
  status: OverrideStatus;
  unit_id?: UnitId5;
  zone_id?: ZoneId3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Plan".
 */
export interface Plan {
  assignments: Assignments;
  based_on_planning_sequence: BasedOnPlanningSequence;
  coverage: Coverage1;
  created_at: CreatedAt;
  created_sim_time_s: CreatedSimTimeS;
  diff: PlanDiff;
  facility_allocations: FacilityAllocations;
  flags: Flags;
  plan_id: PlanId3;
  policy_version: PolicyVersion;
  schema_version: SchemaVersion3;
  session_id: SessionId5;
  soft_consequences: SoftConsequences;
  solver: SolverResult;
  state: PlanState;
  supersedes_approved_plan_id?: SupersedesApprovedPlanId;
  unmet_needs: UnmetNeeds;
  version: Version;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanDiff".
 */
export interface PlanDiff {
  added: Added;
  against_plan_id: AgainstPlanId;
  changed: Changed;
  newly_unmet: NewlyUnmet;
  released: Released;
  totals: DiffTotals;
  unchanged_count: UnchangedCount;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FacilityAllocation".
 */
export interface FacilityAllocation {
  allocation_id: AllocationId;
  facility_id: FacilityId;
  free_after_persons: FreeAfterPersons;
  incident_id: IncidentId6;
  need_id: NeedId5;
  persons: Persons1;
  route?: Route | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PolicyFlag".
 */
export interface PolicyFlag {
  code: Code2;
  flag_id: FlagId;
  incident_id?: IncidentId7;
  message: Message;
  need_id?: NeedId6;
  override_id?: OverrideId1;
  requires_ack: RequiresAck;
  resource_type?: UnitType | null;
  severity: FlagSeverity;
  since_sim_time_s?: SinceSimTimeS;
  zone_id?: ZoneId4;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SoftConsequence".
 */
export interface SoftConsequence {
  delta?: Delta1;
  metric: Metric1;
  need_id?: NeedId7;
  override_id?: OverrideId2;
  zone_id?: ZoneId5;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SolverResult".
 */
export interface SolverResult {
  completed_tiers: CompletedTiers;
  engine: Engine;
  lexicographic_complete: LexicographicComplete;
  objective_vector: ObjectiveVector;
  seed: Seed1;
  status: SolverStatus;
  tie_break_complete: TieBreakComplete;
  wall_time_ms: WallTimeMs;
  workers: Workers;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnmetNeed".
 */
export interface UnmetNeed {
  basis: NeedBasis;
  bridge_candidates?: BridgeCandidates;
  incident_id: IncidentId8;
  need_id: NeedId8;
  quantity_unmet: QuantityUnmet;
  reasons: Reasons4;
  severity: Severity;
  type: NeedType;
  waiting_s: WaitingS;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Hospital".
 */
export interface Hospital {
  capabilities: Capabilities;
  display_name: DisplayName;
  ed_beds_available: EdBedsAvailable;
  facility_id: FacilityId1;
  kind: Kind;
  location: Point;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Shelter".
 */
export interface Shelter {
  capacity_persons: CapacityPersons;
  display_name: DisplayName1;
  facility_id: FacilityId2;
  kind: Kind1;
  location: Point;
  occupied_persons: OccupiedPersons;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodZone".
 */
export interface FloodZone {
  closes_roads: ClosesRoads;
  effective_sim_time_s: EffectiveSimTimeS;
  flood_id: FloodId;
  geometry: Polygon;
  source: Source;
  version: Version1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Polygon".
 */
export interface Polygon {
  coordinates: Coordinates2;
  type: Type2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Incident".
 */
export interface Incident {
  assumed_facts: AssumedFacts;
  category: IncidentCategory;
  created_sim_time_s: CreatedSimTimeS1;
  duplicate_candidate_of: DuplicateCandidateOf;
  incident_id: IncidentId9;
  kind: Kind2;
  location: Point;
  needs: Needs;
  report_ids: ReportIds;
  severity: Severity;
  status: IncidentStatus;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Need".
 */
export interface Need {
  basis: NeedBasis;
  need_id: NeedId9;
  quantity: Quantity;
  reasons: Reasons5;
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
  dangerous_values: DangerousValues;
  limits: PolicyLimits;
  max_debounce_ms: MaxDebounceMs;
  near_arrival_lock_s: NearArrivalLockS;
  objective_tiers: ObjectiveTiers;
  planning_tick_s: PlanningTickS;
  policy_version: PolicyVersion1;
  severity_weights: SeverityWeights;
  solver_budget_ms: SolverBudgetMs;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PolicyCosts".
 */
export interface PolicyCosts {
  als_on_bls: AlsOnBls;
  reassignment: Reassignment;
  reserve_shortfall: ReserveShortfall;
  travel_cap_s: TravelCapS;
  waiting_cap_s: WaitingCapS;
}
export interface DangerousValues {
  [k: string]: "yes" | "no";
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PolicyLimits".
 */
export interface PolicyLimits {
  demand_quanta: DemandQuanta;
  need_records: NeedRecords;
  reserve_pairs: ReservePairs;
  units: Units;
}
export interface SeverityWeights {
  [k: string]: number;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Report".
 */
export interface Report {
  channel: Channel;
  linked_incident_id?: LinkedIncidentId;
  location: Point;
  location_source: LocationSource;
  received_at: ReceivedAt;
  received_sim_time_s: ReceivedSimTimeS;
  report_id: ReportId1;
  text_ref: TextRef;
}
/**
 * Reference to caller text held in the separate, revocable report store (0005).
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TextRef".
 */
export interface TextRef {
  length_chars: LengthChars;
  report_id?: ReportId2;
  store: Store;
  text_sha256: TextSha256;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReserveZone".
 */
export interface ReserveZone {
  coverage_eta_s: CoverageEtaS;
  geometry?: Polygon | null;
  reference_point: Point;
  required_types: RequiredTypes;
  zone_id: ZoneId6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFacts".
 */
export interface TriageFacts1 {
  applicable_facts: ApplicableFacts;
  escalation: Escalation;
  facts: Facts;
  incident_id: IncidentId10;
  policy_version: PolicyVersion2;
  questions_asked: QuestionsAsked;
}
/**
 * Tri-state fact with provenance. ``people_count`` uses ``count`` instead of ``value``.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFact".
 */
export interface TriageFact {
  coerced_from?: FactValue | null;
  coercion_reason?: CoercionReason;
  confirmed_by_operator: ConfirmedByOperator;
  conflict?: Conflict;
  count?: FactCount | null;
  evidence: Evidence;
  key: Key;
  source: FactSource;
  updated_sim_time_s: UpdatedSimTimeS;
  value?: FactValue | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactCount".
 */
export interface FactCount {
  status: CountStatus;
  value: Value;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "EvidenceSpan".
 */
export interface EvidenceSpan {
  end: End;
  report_id: ReportId3;
  start: Start;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "QuestionAsked".
 */
export interface QuestionAsked {
  answer?: FactValue | null;
  asked_sim_time_s: AskedSimTimeS;
  fact_key: FactKey1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Unit".
 */
export interface Unit {
  capacity_persons: CapacityPersons1;
  current_task: CurrentTask | null;
  desired_revision?: DesiredRevision2;
  display_name: DisplayName2;
  home_zone_id: HomeZoneId;
  position: Point;
  position_sim_time_s: PositionSimTimeS;
  status: UnitStatus;
  type: UnitType;
  unit_id: UnitId6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportReceivedEvent".
 */
export interface ReportReceivedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning4;
  aggregate_id: AggregateId4;
  aggregate_type: AggregateType4;
  causation_id: CausationId4;
  correlation_id: CorrelationId4;
  event_id: EventId4;
  event_type: EventType4;
  idempotency_key: IdempotencyKey4;
  occurred_at: OccurredAt4;
  payload: ReportReceivedPayload;
  schema_version: SchemaVersion6;
  sequence: Sequence5;
  session_id: SessionId8;
  sim_time_s: SimTimeS7;
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
  affects_planning: AffectsPlanning5;
  aggregate_id: AggregateId5;
  aggregate_type: AggregateType5;
  causation_id: CausationId5;
  correlation_id: CorrelationId5;
  event_id: EventId5;
  event_type: EventType5;
  idempotency_key: IdempotencyKey5;
  occurred_at: OccurredAt5;
  payload: TriageFactsExtractedPayload;
  schema_version: SchemaVersion7;
  sequence: Sequence6;
  session_id: SessionId9;
  sim_time_s: SimTimeS8;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactsExtractedPayload".
 */
export interface TriageFactsExtractedPayload {
  triage_facts: TriageFacts1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactConfirmedEvent".
 */
export interface TriageFactConfirmedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning6;
  aggregate_id: AggregateId6;
  aggregate_type: AggregateType6;
  causation_id: CausationId6;
  correlation_id: CorrelationId6;
  event_id: EventId6;
  event_type: EventType6;
  idempotency_key: IdempotencyKey6;
  occurred_at: OccurredAt6;
  payload: TriageFactConfirmedPayload;
  schema_version: SchemaVersion8;
  sequence: Sequence7;
  session_id: SessionId10;
  sim_time_s: SimTimeS9;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "TriageFactConfirmedPayload".
 */
export interface TriageFactConfirmedPayload {
  fact: TriageFact;
  incident_id: IncidentId11;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCreatedEvent".
 */
export interface IncidentCreatedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning7;
  aggregate_id: AggregateId7;
  aggregate_type: AggregateType7;
  causation_id: CausationId7;
  correlation_id: CorrelationId7;
  event_id: EventId7;
  event_type: EventType7;
  idempotency_key: IdempotencyKey7;
  occurred_at: OccurredAt7;
  payload: IncidentPayload;
  schema_version: SchemaVersion9;
  sequence: Sequence8;
  session_id: SessionId11;
  sim_time_s: SimTimeS10;
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
  affects_planning: AffectsPlanning8;
  aggregate_id: AggregateId8;
  aggregate_type: AggregateType8;
  causation_id: CausationId8;
  correlation_id: CorrelationId8;
  event_id: EventId8;
  event_type: EventType8;
  idempotency_key: IdempotencyKey8;
  occurred_at: OccurredAt8;
  payload: IncidentPayload;
  schema_version: SchemaVersion10;
  sequence: Sequence9;
  session_id: SessionId12;
  sim_time_s: SimTimeS11;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCategoryChangedEvent".
 */
export interface IncidentCategoryChangedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning9;
  aggregate_id: AggregateId9;
  aggregate_type: AggregateType9;
  causation_id: CausationId9;
  correlation_id: CorrelationId9;
  event_id: EventId9;
  event_type: EventType9;
  idempotency_key: IdempotencyKey9;
  occurred_at: OccurredAt9;
  payload: IncidentCategoryChangedPayload;
  schema_version: SchemaVersion11;
  sequence: Sequence10;
  session_id: SessionId13;
  sim_time_s: SimTimeS12;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentCategoryChangedPayload".
 */
export interface IncidentCategoryChangedPayload {
  from_category: IncidentCategory;
  incident: Incident;
  reason: Reason;
  triggering_fact_keys: TriggeringFactKeys;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportLinkedToIncidentEvent".
 */
export interface ReportLinkedToIncidentEvent {
  actor: Actor;
  affects_planning: AffectsPlanning10;
  aggregate_id: AggregateId10;
  aggregate_type: AggregateType10;
  causation_id: CausationId10;
  correlation_id: CorrelationId10;
  event_id: EventId10;
  event_type: EventType10;
  idempotency_key: IdempotencyKey10;
  occurred_at: OccurredAt10;
  payload: ReportLinkedToIncidentPayload;
  schema_version: SchemaVersion12;
  sequence: Sequence11;
  session_id: SessionId14;
  sim_time_s: SimTimeS13;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportLinkedToIncidentPayload".
 */
export interface ReportLinkedToIncidentPayload {
  incident_id: IncidentId12;
  report_id: ReportId4;
  resolution: Resolution1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentResolvedEvent".
 */
export interface IncidentResolvedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning11;
  aggregate_id: AggregateId11;
  aggregate_type: AggregateType11;
  causation_id: CausationId11;
  correlation_id: CorrelationId11;
  event_id: EventId11;
  event_type: EventType11;
  idempotency_key: IdempotencyKey11;
  occurred_at: OccurredAt11;
  payload: IncidentResolvedPayload;
  schema_version: SchemaVersion13;
  sequence: Sequence12;
  session_id: SessionId15;
  sim_time_s: SimTimeS14;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "IncidentResolvedPayload".
 */
export interface IncidentResolvedPayload {
  incident_id: IncidentId13;
  invalidates_assignment_ids: InvalidatesAssignmentIds;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusChangedEvent".
 */
export interface UnitStatusChangedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning12;
  aggregate_id: AggregateId12;
  aggregate_type: AggregateType12;
  causation_id: CausationId12;
  correlation_id: CorrelationId12;
  event_id: EventId12;
  event_type: EventType12;
  idempotency_key: IdempotencyKey12;
  occurred_at: OccurredAt12;
  payload: UnitStatusChangedPayload;
  schema_version: SchemaVersion14;
  sequence: Sequence13;
  session_id: SessionId16;
  sim_time_s: SimTimeS15;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusChangedPayload".
 */
export interface UnitStatusChangedPayload {
  invalidates_assignment_ids: InvalidatesAssignmentIds1;
  unit: Unit;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanningTickCommittedEvent".
 */
export interface PlanningTickCommittedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning13;
  aggregate_id: AggregateId13;
  aggregate_type: AggregateType13;
  causation_id: CausationId13;
  correlation_id: CorrelationId13;
  event_id: EventId13;
  event_type: EventType13;
  idempotency_key: IdempotencyKey13;
  occurred_at: OccurredAt13;
  payload: PlanningTickCommittedPayload;
  schema_version: SchemaVersion15;
  sequence: Sequence14;
  session_id: SessionId17;
  sim_time_s: SimTimeS16;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanningTickCommittedPayload".
 */
export interface PlanningTickCommittedPayload {
  tick_sim_time_s: TickSimTimeS;
  units: Units2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitPlanningState".
 */
export interface UnitPlanningState {
  lock: Lock;
  position: Point;
  remaining_route_s: RemainingRouteS;
  unit_id: UnitId7;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodZoneUpdatedEvent".
 */
export interface FloodZoneUpdatedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning14;
  aggregate_id: AggregateId14;
  aggregate_type: AggregateType14;
  causation_id: CausationId14;
  correlation_id: CorrelationId14;
  event_id: EventId14;
  event_type: EventType14;
  idempotency_key: IdempotencyKey14;
  occurred_at: OccurredAt14;
  payload: FloodZoneUpdatedPayload;
  schema_version: SchemaVersion16;
  sequence: Sequence15;
  session_id: SessionId18;
  sim_time_s: SimTimeS17;
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
  affects_planning: AffectsPlanning15;
  aggregate_id: AggregateId15;
  aggregate_type: AggregateType15;
  causation_id: CausationId15;
  correlation_id: CorrelationId15;
  event_id: EventId15;
  event_type: EventType15;
  idempotency_key: IdempotencyKey15;
  occurred_at: OccurredAt15;
  payload: RoadClosureUpdatedPayload;
  schema_version: SchemaVersion17;
  sequence: Sequence16;
  session_id: SessionId19;
  sim_time_s: SimTimeS18;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RoadClosureUpdatedPayload".
 */
export interface RoadClosureUpdatedPayload {
  closed: Closed;
  closure_id: ClosureId;
  geometry: Geometry;
  version: Version2;
}
export interface Geometry {
  [k: string]: unknown;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FacilityCapacityUpdatedEvent".
 */
export interface FacilityCapacityUpdatedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning16;
  aggregate_id: AggregateId16;
  aggregate_type: AggregateType16;
  causation_id: CausationId16;
  correlation_id: CorrelationId16;
  event_id: EventId16;
  event_type: EventType16;
  idempotency_key: IdempotencyKey16;
  occurred_at: OccurredAt16;
  payload: FacilityCapacityUpdatedPayload;
  schema_version: SchemaVersion18;
  sequence: Sequence17;
  session_id: SessionId20;
  sim_time_s: SimTimeS19;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FacilityCapacityUpdatedPayload".
 */
export interface FacilityCapacityUpdatedPayload {
  ed_beds_available?: EdBedsAvailable1;
  facility_id: FacilityId3;
  occupied_persons?: OccupiedPersons1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideAcceptedEvent".
 */
export interface OverrideAcceptedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning17;
  aggregate_id: AggregateId17;
  aggregate_type: AggregateType17;
  causation_id: CausationId17;
  correlation_id: CorrelationId17;
  event_id: EventId17;
  event_type: EventType17;
  idempotency_key: IdempotencyKey17;
  occurred_at: OccurredAt17;
  payload: OverridePayload;
  schema_version: SchemaVersion19;
  sequence: Sequence18;
  session_id: SessionId21;
  sim_time_s: SimTimeS20;
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
  affects_planning: AffectsPlanning18;
  aggregate_id: AggregateId18;
  aggregate_type: AggregateType18;
  causation_id: CausationId18;
  correlation_id: CorrelationId18;
  event_id: EventId18;
  event_type: EventType18;
  idempotency_key: IdempotencyKey18;
  occurred_at: OccurredAt18;
  payload: OverrideEndedPayload;
  schema_version: SchemaVersion20;
  sequence: Sequence19;
  session_id: SessionId22;
  sim_time_s: SimTimeS21;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideEndedPayload".
 */
export interface OverrideEndedPayload {
  override_id: OverrideId3;
  reason: Reason1;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRevokedEvent".
 */
export interface OverrideRevokedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning19;
  aggregate_id: AggregateId19;
  aggregate_type: AggregateType19;
  causation_id: CausationId19;
  correlation_id: CorrelationId19;
  event_id: EventId19;
  event_type: EventType19;
  idempotency_key: IdempotencyKey19;
  occurred_at: OccurredAt19;
  payload: OverrideEndedPayload;
  schema_version: SchemaVersion21;
  sequence: Sequence20;
  session_id: SessionId23;
  sim_time_s: SimTimeS22;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanApprovedEvent".
 */
export interface PlanApprovedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning20;
  aggregate_id: AggregateId20;
  aggregate_type: AggregateType20;
  causation_id: CausationId20;
  correlation_id: CorrelationId20;
  event_id: EventId20;
  event_type: EventType20;
  idempotency_key: IdempotencyKey20;
  occurred_at: OccurredAt20;
  payload: PlanApprovedPayload;
  schema_version: SchemaVersion22;
  sequence: Sequence21;
  session_id: SessionId24;
  sim_time_s: SimTimeS23;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanApprovedPayload".
 */
export interface PlanApprovedPayload {
  acknowledged_flag_ids: AcknowledgedFlagIds1;
  based_on_planning_sequence: BasedOnPlanningSequence1;
  desired_assignments: DesiredAssignments;
  note_present?: NotePresent;
  outbox_keys: OutboxKeys1;
  plan_id: PlanId4;
  version: Version3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchSentEvent".
 */
export interface SimulatedDispatchSentEvent {
  actor: Actor;
  affects_planning: AffectsPlanning21;
  aggregate_id: AggregateId21;
  aggregate_type: AggregateType21;
  causation_id: CausationId21;
  correlation_id: CorrelationId21;
  event_id: EventId21;
  event_type: EventType21;
  idempotency_key: IdempotencyKey21;
  occurred_at: OccurredAt21;
  payload: SimulatedDispatchSentPayload;
  schema_version: SchemaVersion23;
  sequence: Sequence22;
  session_id: SessionId25;
  sim_time_s: SimTimeS24;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchSentPayload".
 */
export interface SimulatedDispatchSentPayload {
  action: DispatchAction;
  assignment_id: AssignmentId4;
  outbox_key: OutboxKey1;
  simulated: Simulated1;
  unit_after?: Unit | null;
  unit_id?: UnitId8;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitPositionObservedEvent".
 */
export interface UnitPositionObservedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning22;
  aggregate_id: AggregateId22;
  aggregate_type: AggregateType22;
  causation_id: CausationId22;
  correlation_id: CorrelationId22;
  event_id: EventId22;
  event_type: EventType22;
  idempotency_key: IdempotencyKey22;
  occurred_at: OccurredAt22;
  payload: UnitPositionObservedPayload;
  schema_version: SchemaVersion24;
  sequence: Sequence23;
  session_id: SessionId26;
  sim_time_s: SimTimeS25;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitPositionObservedPayload".
 */
export interface UnitPositionObservedPayload {
  observed_sim_time_s: ObservedSimTimeS;
  position: Point;
  unit_id: UnitId9;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanProposedEvent".
 */
export interface PlanProposedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning23;
  aggregate_id: AggregateId23;
  aggregate_type: AggregateType23;
  causation_id: CausationId23;
  correlation_id: CorrelationId23;
  event_id: EventId23;
  event_type: EventType23;
  idempotency_key: IdempotencyKey23;
  occurred_at: OccurredAt23;
  payload: PlanProposedPayload;
  schema_version: SchemaVersion25;
  sequence: Sequence24;
  session_id: SessionId27;
  sim_time_s: SimTimeS26;
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
  affects_planning: AffectsPlanning24;
  aggregate_id: AggregateId24;
  aggregate_type: AggregateType24;
  causation_id: CausationId24;
  correlation_id: CorrelationId24;
  event_id: EventId24;
  event_type: EventType24;
  idempotency_key: IdempotencyKey24;
  occurred_at: OccurredAt24;
  payload: PlanSupersededPayload;
  schema_version: SchemaVersion26;
  sequence: Sequence25;
  session_id: SessionId28;
  sim_time_s: SimTimeS27;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanSupersededPayload".
 */
export interface PlanSupersededPayload {
  plan_id: PlanId5;
  reason: Reason2;
  superseded_by_plan_id: SupersededByPlanId;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanRevalidatedEvent".
 */
export interface PlanRevalidatedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning25;
  aggregate_id: AggregateId25;
  aggregate_type: AggregateType25;
  causation_id: CausationId25;
  correlation_id: CorrelationId25;
  event_id: EventId25;
  event_type: EventType25;
  idempotency_key: IdempotencyKey25;
  occurred_at: OccurredAt25;
  payload: PlanRevalidatedPayload;
  schema_version: SchemaVersion27;
  sequence: Sequence26;
  session_id: SessionId29;
  sim_time_s: SimTimeS28;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanRevalidatedPayload".
 */
export interface PlanRevalidatedPayload {
  checked_planning_sequence: CheckedPlanningSequence;
  checked_sim_time_s: CheckedSimTimeS;
  plan_id: PlanId6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanFailedEvent".
 */
export interface PlanFailedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning26;
  aggregate_id: AggregateId26;
  aggregate_type: AggregateType26;
  causation_id: CausationId26;
  correlation_id: CorrelationId26;
  event_id: EventId26;
  event_type: EventType26;
  idempotency_key: IdempotencyKey26;
  occurred_at: OccurredAt26;
  payload: PlanFailedPayload;
  schema_version: SchemaVersion28;
  sequence: Sequence27;
  session_id: SessionId30;
  sim_time_s: SimTimeS29;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "PlanFailedPayload".
 */
export interface PlanFailedPayload {
  based_on_planning_sequence: BasedOnPlanningSequence2;
  plan_id: PlanId7;
  reasons: Reasons6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRejectedEvent".
 */
export interface OverrideRejectedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning27;
  aggregate_id: AggregateId27;
  aggregate_type: AggregateType27;
  causation_id: CausationId27;
  correlation_id: CorrelationId27;
  event_id: EventId27;
  event_type: EventType27;
  idempotency_key: IdempotencyKey27;
  occurred_at: OccurredAt27;
  payload: OverrideRejectedPayload;
  schema_version: SchemaVersion29;
  sequence: Sequence28;
  session_id: SessionId31;
  sim_time_s: SimTimeS30;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRejectedPayload".
 */
export interface OverrideRejectedPayload {
  bridges_need_id?: BridgesNeedId2;
  conflicts: Conflicts;
  incident_id?: IncidentId14;
  kind: OverrideKind;
  need_id?: NeedId10;
  override_id: OverrideId5;
  unit_id?: UnitId11;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideConflict".
 */
export interface OverrideConflict {
  code: Code3;
  detail: Detail;
  override_id?: OverrideId4;
  unit_id?: UnitId10;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchQueuedEvent".
 */
export interface SimulatedDispatchQueuedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning28;
  aggregate_id: AggregateId28;
  aggregate_type: AggregateType28;
  causation_id: CausationId28;
  correlation_id: CorrelationId28;
  event_id: EventId28;
  event_type: EventType28;
  idempotency_key: IdempotencyKey28;
  occurred_at: OccurredAt28;
  payload: SimulatedDispatchQueuedPayload;
  schema_version: SchemaVersion30;
  sequence: Sequence29;
  session_id: SessionId32;
  sim_time_s: SimTimeS31;
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
  affects_planning: AffectsPlanning29;
  aggregate_id: AggregateId29;
  aggregate_type: AggregateType29;
  causation_id: CausationId29;
  correlation_id: CorrelationId29;
  event_id: EventId29;
  event_type: EventType29;
  idempotency_key: IdempotencyKey29;
  occurred_at: OccurredAt29;
  payload: SimulatedDispatchEndedPayload;
  schema_version: SchemaVersion31;
  sequence: Sequence30;
  session_id: SessionId33;
  sim_time_s: SimTimeS32;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchEndedPayload".
 */
export interface SimulatedDispatchEndedPayload {
  attempts?: Attempts;
  outbox_key: OutboxKey2;
  reason: Reason3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "SimulatedDispatchFailedEvent".
 */
export interface SimulatedDispatchFailedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning30;
  aggregate_id: AggregateId30;
  aggregate_type: AggregateType30;
  causation_id: CausationId30;
  correlation_id: CorrelationId30;
  event_id: EventId30;
  event_type: EventType30;
  idempotency_key: IdempotencyKey30;
  occurred_at: OccurredAt30;
  payload: SimulatedDispatchEndedPayload;
  schema_version: SchemaVersion32;
  sequence: Sequence31;
  session_id: SessionId34;
  sim_time_s: SimTimeS33;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessGrantedEvent".
 */
export interface MedicalProfileAccessGrantedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning31;
  aggregate_id: AggregateId31;
  aggregate_type: AggregateType31;
  causation_id: CausationId31;
  correlation_id: CorrelationId31;
  event_id: EventId31;
  event_type: EventType31;
  idempotency_key: IdempotencyKey31;
  occurred_at: OccurredAt31;
  payload: MedicalProfileAccessPayload;
  schema_version: SchemaVersion33;
  sequence: Sequence32;
  session_id: SessionId35;
  sim_time_s: SimTimeS34;
}
/**
 * Audit record: field *names* only, never profile values.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessPayload".
 */
export interface MedicalProfileAccessPayload {
  granted_fields: GrantedFields;
  incident_id: IncidentId15;
  profile_ref: ProfileRef;
  reason?: Reason4;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessDeniedEvent".
 */
export interface MedicalProfileAccessDeniedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning32;
  aggregate_id: AggregateId32;
  aggregate_type: AggregateType32;
  causation_id: CausationId32;
  correlation_id: CorrelationId32;
  event_id: EventId32;
  event_type: EventType32;
  idempotency_key: IdempotencyKey32;
  occurred_at: OccurredAt32;
  payload: MedicalProfileAccessPayload;
  schema_version: SchemaVersion34;
  sequence: Sequence33;
  session_id: SessionId36;
  sim_time_s: SimTimeS35;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "HospitalPreAlertSimulatedEvent".
 */
export interface HospitalPreAlertSimulatedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning33;
  aggregate_id: AggregateId33;
  aggregate_type: AggregateType33;
  causation_id: CausationId33;
  correlation_id: CorrelationId33;
  event_id: EventId33;
  event_type: EventType33;
  idempotency_key: IdempotencyKey33;
  occurred_at: OccurredAt33;
  payload: HospitalPreAlertSimulatedPayload;
  schema_version: SchemaVersion35;
  sequence: Sequence34;
  session_id: SessionId37;
  sim_time_s: SimTimeS36;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "HospitalPreAlertSimulatedPayload".
 */
export interface HospitalPreAlertSimulatedPayload {
  capability_needed?: CapabilityNeeded;
  hospital_id: HospitalId;
  incident_id: IncidentId16;
  outbox_key: OutboxKey3;
  simulated: Simulated2;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ModelAdapterDegradedEvent".
 */
export interface ModelAdapterDegradedEvent {
  actor: Actor;
  affects_planning: AffectsPlanning34;
  aggregate_id: AggregateId34;
  aggregate_type: AggregateType34;
  causation_id: CausationId34;
  correlation_id: CorrelationId34;
  event_id: EventId34;
  event_type: EventType34;
  idempotency_key: IdempotencyKey34;
  occurred_at: OccurredAt34;
  payload: ModelAdapterDegradedPayload;
  schema_version: SchemaVersion36;
  sequence: Sequence35;
  session_id: SessionId38;
  sim_time_s: SimTimeS37;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ModelAdapterDegradedPayload".
 */
export interface ModelAdapterDegradedPayload {
  adapter: Adapter;
  cause: Cause;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FactConfirmCommand".
 */
export interface FactConfirmCommand {
  count?: Count;
  expected_session_id: ExpectedSessionId6;
  reason_text: ReasonText2;
  value?: FactValue | null;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodAccepted".
 */
export interface FloodAccepted {
  flood_id: FloodId1;
  sequence: Sequence36;
  version: Version4;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "FloodEventCommand".
 */
export interface FloodEventCommand {
  closes_roads: ClosesRoads1;
  effective_sim_time_s: EffectiveSimTimeS1;
  expected_session_id: ExpectedSessionId7;
  flood_id: FloodId2;
  geometry: Polygon;
  version: Version5;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "HealthResponse".
 */
export interface HealthResponse {
  degraded: Degraded;
  llm_provider: LlmProvider;
  mode: Mode;
  routing_provider: RoutingProvider;
  schema_version: SchemaVersion37;
  status: Status;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "MedicalProfileAccessCommand".
 */
export interface MedicalProfileAccessCommand {
  expected_session_id: ExpectedSessionId8;
  operator_reason: OperatorReason;
  profile_ref: ProfileRef1;
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
  profile_ref: ProfileRef2;
  subject_ref: SubjectRef;
  synthetic: Synthetic;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideCommand".
 */
export interface OverrideCommand {
  bridges_need_id?: BridgesNeedId3;
  expected_plan_id: ExpectedPlanId;
  expected_planning_sequence: ExpectedPlanningSequence1;
  expected_session_id: ExpectedSessionId9;
  incident_id?: IncidentId17;
  kind: OverrideKind;
  need_id?: NeedId11;
  reason_text: ReasonText3;
  replaces_override_id?: ReplacesOverrideId1;
  revokes_override_id?: RevokesOverrideId1;
  unit_id?: UnitId12;
  zone_id?: ZoneId7;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "OverrideRecorded".
 */
export interface OverrideRecorded {
  override_id: OverrideId6;
  recompute: Recompute;
  sequence: Sequence37;
  status: Status1;
}
/**
 * RFC 9457 problem details with a stable machine ``code`` (0001).
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "Problem".
 */
export interface Problem {
  code: Code4;
  conflicts?: Conflicts1;
  current?: Current;
  detail?: Detail1;
  errors?: Errors;
  instance?: Instance;
  missing_flag_ids?: MissingFlagIds;
  override_id?: OverrideId7;
  reason?: Reason5;
  status: Status2;
  title: Title;
  type: Type3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ProblemFieldError".
 */
export interface ProblemFieldError {
  message: Message1;
  pointer: Pointer;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RecomputeAccepted".
 */
export interface RecomputeAccepted {
  planning_sequence: PlanningSequence1;
  status: Status3;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "RecomputeCommand".
 */
export interface RecomputeCommand {
  expected_session_id: ExpectedSessionId10;
  reason: Reason6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportAccepted".
 */
export interface ReportAccepted {
  escalated: Escalated1;
  incident_id: IncidentId18;
  report_id: ReportId5;
  sequence: Sequence38;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "ReportCommand".
 */
export interface ReportCommand {
  channel: Channel1;
  expected_session_id: ExpectedSessionId11;
  location: Point;
  location_source: LocationSource1;
  sim_time_s: SimTimeS38;
  text: Text;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusAccepted".
 */
export interface UnitStatusAccepted {
  invalidated_assignment_ids: InvalidatedAssignmentIds;
  sequence: Sequence39;
  status: UnitStatus;
  unit_id: UnitId13;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "UnitStatusCommand".
 */
export interface UnitStatusCommand {
  expected_session_id: ExpectedSessionId12;
  position?: Point | null;
  sim_time_s: SimTimeS39;
  to_status: UnitStatus;
}
/**
 * Server confirms backlog delivery; clients enable commands only after this.
 *
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsCaughtUp".
 */
export interface WsCaughtUp {
  head_sequence: HeadSequence2;
  type: Type4;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsEvent".
 */
export interface WsEvent {
  event: Event;
  type: Type5;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsHeartbeat".
 */
export interface WsHeartbeat {
  head_sequence: HeadSequence3;
  type: Type6;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsHello".
 */
export interface WsHello {
  head_sequence: HeadSequence4;
  schema_version: SchemaVersion38;
  session_id: SessionId39;
  type: Type7;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsSnapshotRequired".
 */
export interface WsSnapshotRequired {
  session_id: SessionId40;
  type: Type8;
}
/**
 * This interface was referenced by `CrisisCommandContracts`'s JSON-Schema
 * via the `definition` "WsSubscribe".
 */
export interface WsSubscribe {
  after_sequence: AfterSequence;
  session_id: SessionId41;
  type: Type9;
}
