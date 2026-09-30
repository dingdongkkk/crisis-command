# 0005 — Plan lifecycle, approval, dispatch and replay

Status: accepted (CC-01), revised after Codex review — see [0009](0009-review-resolutions.md). Consumers: CC-03, CC-08, CC-09.

## Events drive everything

Envelope fields are required unless explicitly optional:

| Field | Type / rule |
| --- | --- |
| `schema_version` | string `1.0` |
| `event_id` | UUIDv4 |
| `session_id` | active simulation ID |
| `sequence` | gapless integer ≥1 within that session |
| `event_type` | catalog discriminator |
| `aggregate_type`, `aggregate_id` | stable strings |
| `occurred_at` | UTC RFC3339, millisecond precision, `Z` |
| `sim_time_s` | nonnegative integer |
| `actor` | `{kind,id}`; kind: operator/caller_sim/system/solver/watchdog/rule_adapter/model_adapter |
| `correlation_id` | string |
| `causation_id` | optional UUIDv4 or null |
| `idempotency_key` | string or null; unique event effect identity within a session |
| `affects_planning` | fixed by catalog, never chosen by client/model |
| `payload` | closed typed object selected by event_type |

### Catalog (draft v1.0)

Planning: `SessionStarted`, `ReportReceived`, `TriageFactsExtracted`, `TriageFactConfirmed`, `IncidentCreated`, `IncidentAssessed`, `IncidentCategoryChanged`, `ReportLinkedToIncident`, `IncidentResolved`, `UnitStatusChanged`, `PlanningTickCommitted`, `FloodZoneUpdated`, `RoadClosureUpdated`, `FacilityCapacityUpdated`, `OverrideAccepted`, `OverrideInvalidated`, `OverrideRevoked`, `PlanApproved`, `SimulatedDispatchSent`.

Non-planning: `UnitPositionObserved`, `EscalatedToHuman`, `DuplicateCandidateFlagged`, `PlanProposed`, `PlanSuperseded`, `PlanRevalidated`, `PlanFailed`, `ApprovalRejected`, `OverrideRejected`, `SimulatedDispatchQueued`, `SimulatedDispatchCancelled`, `SimulatedDispatchFailed`, `MedicalProfileAccessGranted`, `MedicalProfileAccessDenied`, `HospitalPreAlertSimulated`, `ModelAdapterDegraded`.

A failure/cancellation which invalidates capacity or a unit's availability also appends the corresponding planning-relevant domain event in the same transaction. Delivery receipts alone cannot silently change planning state.

### Position updates and scheduler liveness

- `UnitPositionObserved` records raw display telemetry only. It cannot mutate planning positions, ETAs or locks. UI distinguishes observed positions from the timestamped planning snapshot.
- Every global 10-s simulation boundary, commit **one** `PlanningTickCommitted` containing all units' latest positions, remaining route times and locks, plus the new simulation time. All units share the boundary; no per-unit timers. This event also advances waiting-age calculations. At 1× simulation speed a 2 s solve plus ≤250 ms initial debounce leaves at least 7.75 s before the next ordinary planning tick.
- Arrival, crossing the 120 s lock threshold, breakdown, route invalidation, incident/override changes and capacity changes are material: commit immediately, flushing relevant pending observations into the same transaction. These events can legitimately stale a proposal; never defer a safety-relevant transition to create an approval window.
- Recompute starts no later than 250 ms after the first material event, even if more arrive. One solve runs at a time; later events set a dirty/latest-sequence marker rather than resetting a trailing debounce forever. Discard stale solver results and schedule the latest snapshot immediately. A continuous stream of material emergencies has no promised approval window; show `world_changing` and allow the operator to pause synthetic scenario progression.
- Pausing/accelerating is a simulator control: default ≤1× while awaiting operator decisions, accelerated playback is read-only. The UI cannot approve during accelerated replay. Wall-clock debounce/busy handling never affects the deterministic event projection.
- Before returning the transactionally consistent world used by an approval, apply any already-observed material transition. Non-material sub-tick ETA drift is a documented ≤10 simulated-second approximation; hard validity/lock changes are never treated as non-material.

### Privacy

Free report text lives in a separate revocable report store. Events store its reference/hash/length and evidence offsets, never the text or medical profile values. Plan documents contain only synthetic IDs, numbers, enum codes, flags and reason facts. Profile access events and command receipts store granted field names, not values. Replay restores operational state without restoring revoked text/profile data.

## Plan lifecycle and semantic equality

`computing → proposed → approved → dispatching → dispatched_simulated`; proposed may become superseded/failed; delivery may produce `dispatch_partial_failed`.

- Plans contain schema/session IDs, version, based-on planning sequence, policy version, creation times, assignments, facility allocations, unmet quantities, flags, reason facts, coverage results, diff and solver result.
- `PlanProposed.payload.plan` embeds the **complete immutable plan**, including recorded route results/route IDs needed by the display. No opaque external `plan_ref` is sufficient. Historical plans are derived from these event payloads; database plan tables are rebuildable projections.
- A material event makes older proposals stale immediately. Atomically supersede any previous proposal when publishing the replacement. Only one current proposal exists. Publishing a result requires its input planning sequence still to be current.
- Recompute may skip a fresh approval only when the full operator-visible decision is semantically equal to the approved decision. Compare targets, roles, quantities, facility allocations, route/flood versions and validity, locks, ETA values, unmet needs/bases/reasons, coverage, active-override consequences, policy version, flags (severity/ack/code/subject), and solver degradation guarantees. Ignore only generated plan/assignment/flag IDs, creation timestamps, solver timing and wording derived from the same reason facts. Every operationally meaningful difference produces a new proposal, even when unit targets do not change.
- An equal result emits non-planning `PlanRevalidated{plan_id, checked_planning_sequence, checked_sim_time_s}`. This records freshness without overwriting the original approval or losing replay equivalence. It also supersedes any obsolete pending proposal. New generated IDs do not by themselves force reapproval; compare normalized semantic identities.
- Approved is desired state, not observed execution. Unit `current_task` changes only through recorded delivery or a domain invalidation (breakdown/resolution). If no new valid plan exists, keep only still-valid tasks from the old approved plan; never preserve a broken unit's task just because recompute failed.

## Approval: atomic check and append

`POST /plans/{plan_id}/approve` body: `expected_session_id`, `expected_plan_version`, `expected_planning_sequence`, `acknowledged_flag_ids`, optional note. See the complete request in `examples/api.examples.json`.

Use `BEGIN IMMEDIATE` with receipt lookup and all state reads in the same database transaction. Do not read eligibility from an independently lagging in-memory projection. Routing/solver/model calls run before this transaction, not while holding its write lock.

1. Apply 0001 receipt lookup and session validation. Same-key retry returns the original result even though the plan is now approved.
2. Plan exists in that session, else 404. Already-approved/dispatched plans return `PLAN_NOT_PROPOSED` for a new command key. Superseded or outdated proposals return `STALE_PLAN` (this precedence also applies to examples).
3. Require `expected_plan_version == plan.version` and `expected_planning_sequence == plan.based_on_planning_sequence == current planning_sequence`, and require this plan to be the current proposal.
4. Require acknowledgement of every current `requires_ack` flag; reject unknown flag IDs as validation errors. Re-validate H1–H8 against transactional current state, including material transitions.
5. Append `PlanApproved`, update the desired assignment revision for each unit, and append queued **assign/release** commands for the difference from actual execution/pending work. Do not simply diff desired plans: a previously undelivered command may still need execution. Retain unchanged compatible pending commands; cancel obsolete ones. Persist the command receipt, events, projections and outbox rows atomically.

Domain rejections append `ApprovalRejected` (non-planning) and save the rejection receipt. A stale-session rejection must not append into the new session. Handle `SQLITE_BUSY` with a bounded total 1 s acquisition budget; on exhaustion return 503 `DATABASE_BUSY`, `Retry-After: 1`, without recording a terminal command receipt. Retry the same key after reacquiring the lock and reread all state. Two distinct approvals serialize: at most one succeeds. A database failure rolls back event/outbox/receipt/projection writes together.

Whole-plan approval only. No automatic dispatch approval. Losing a race to a breakdown cannot result in a queued or executed invalid assignment.

## Simulated outbox and assignment fencing

- Each command has `session_id`, `outbox_key`, `action: assign|release|hospital_pre_alert`, `unit_id` where applicable, `assignment_id`, `desired_revision`, approved `plan_id`, payload and delivery state. Key is `session_id:plan_id:action:assignment_id` (for a facility alert use its stable alert ID instead of assignment ID). Release names the old assignment. IDs alone do not establish that a command is still current.
- Approval sets authoritative desired assignments/revisions. Breakdown, resolution, invalidated route or a newer approved target updates the affected revision and cancels incompatible pending commands atomically. Reset cancels every pending command from the previous session. Unchanged targets may retain their revision; no blanket equality to global planning sequence is required because other valid deliveries advance that sequence.
- The worker opens `BEGIN IMMEDIATE`, reads the undelivered command and current state, and checks active session, desired revision, target identity, hard eligibility/locks and route/facility validity. On mismatch append `SimulatedDispatchCancelled{outbox_key,reason}` and mark cancelled; never emit Sent. A release is valid only for the named current assignment; it cannot clear a newer task. A broken unit stays broken when its task is released.
- The sender is a pure in-process event constructor with **no side effect before commit**. In the same transaction append `SimulatedDispatchSent{outbox_key,action,unit_id,assignment_id,unit_after}` and update delivery/projection. `unit_after` records the complete affected operational unit state for replay. Unique `(session_id, outbox_key, terminal outcome)` and a single terminal-state transition prevent concurrent success/failure/cancellation; an already-terminal command returns its recorded outcome. A crash before commit has no effect; a crash after commit followed by retry cannot move the unit again.
- Retryable errors leave the command pending with bounded retry metadata; exhaustion appends `SimulatedDispatchFailed{outbox_key,reason,attempts}` and marks failed. Retrying terminal failures requires a newly approved command, not deletion of the original event. Tests cover two workers, crash boundaries, obsolete commands, release ordering and reset.
- Plan dispatch state is derived: zero outstanding commands means dispatched; pending commands mean dispatching; terminal failures/cancellations mean partial failure unless a later recorded plan/revalidation explicitly supersedes the command. A plan with no changed execution commands is dispatched immediately from PlanApproved.
- Hospital pre-alerts use the same session/revision/receipt checks; `HospitalPreAlertSimulated` is the terminal event and records only synthetic facts. No network/real transport exists.

## Replay contract

`state = fold(apply, events[1..n])`. `SessionStarted` includes the complete synthetic initial world and policy, or an embedded seed snapshot; a seed name alone is insufficient. `PlanProposed` embeds its plan; triage and assessment events carry their complete resulting facts/needs; unit/facility/flood events carry resulting values. IDs may reference earlier events in the same log, never an unavailable mutable external store.

Replaying never runs the outbox sender, solver, router or model, nor emits new events. Rebuild outbox status from Queued/Sent/Cancelled/Failed events and execution from their recorded results. Derived plan tables and unit revisions must hash identically to live projections. Exclude wall-clock connection state, raw report text and profile values from the operational state hash. CC-03 must test full sequence-1 replay and snapshot-plus-suffix equivalence, including partial failure/cancellation and revalidation.

The draft example provides a complete suffix 53–67 with an explicit checkpoint at 52. It demonstrates recorded plan/fact/dispatch inputs, not a claim that a full application replay engine already exists.

## Snapshot and delivery protocol

- `GET /state[?at_sequence=n&session_id=s]` returns schema/session IDs, as-of/planning sequence, simulation time, incidents, units, facilities, flood, reserve zones, active overrides, **embedded** nullable `approved_plan` and `current_proposal`, and pending/terminal outbox state. Replay requests must identify the session. The checkpoint example has additional historical plans needed to resolve suffix references; normal snapshots may omit those and clients fetch historical plans by session-qualified ID.
- `GET /events?after_sequence=n&session_id=s&limit=500` requires session; wrong session/history outside retention yields 410 `SNAPSHOT_REQUIRED`.
- WebSocket hello identifies session/head/schema. Subscribe supplies session and after_sequence. Server sends backlog then ordered envelopes and a heartbeat every 10 wall seconds. Subscribe begins buffering live events before backlog retrieval to avoid a gap.
- Client applies only `last+1`, ignores duplicates ≤last in the same session, and resyncs on gaps or session changes. Session check precedes sequence comparison. Resync fetches one consistent snapshot and subscribes after its sequence; command controls stay disabled until the server confirms backlog catch-up. No traffic for 30 wall seconds means disconnected; reconnect backoff 1/2/4/8 s.
