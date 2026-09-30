# 0005 — Plan lifecycle, stale approval, simulated dispatch and replay

Status: accepted (CC-01). Consumers: CC-03 event store, CC-08 approval/outbox, CC-04/CC-09 UI.

## Events drive everything

Envelope (all fields required unless marked):

| Field | Type | Notes |
| --- | --- | --- |
| `schema_version` | string | `"1.0"` |
| `event_id` | UUIDv4 | |
| `session_id` | string | changes on demo reset |
| `sequence` | int ≥ 1 | gapless per session, assigned in the append transaction |
| `event_type` | enum | catalog below |
| `aggregate_type` / `aggregate_id` | string | e.g. `plan` / `plan_0007` |
| `occurred_at` | RFC 3339 UTC | wall clock, informational |
| `sim_time_s` | int | simulation clock |
| `actor` | `{kind, id}` | `kind`: `operator`, `caller_sim`, `system`, `solver`, `watchdog`, `rule_adapter`, `model_adapter` |
| `correlation_id` | string | groups a command and its consequences |
| `causation_id` | UUID, optional | event that caused this one |
| `idempotency_key` | string or null | 0001 |
| `affects_planning` | bool | copied from catalog |
| `payload` | object | typed per `event_type`; minimum synthetic references only |

### Catalog (v1.0)

`affects_planning: true` — `ReportReceived`, `TriageFactsExtracted`, `TriageFactConfirmed`, `IncidentCreated`, `IncidentAssessed`, `IncidentCategoryChanged`, `ReportLinkedToIncident`, `IncidentResolved`, `UnitStatusChanged`, `UnitPositionUpdated`, `FloodZoneUpdated`, `RoadClosureUpdated`, `FacilityCapacityUpdated`, `OverrideAccepted`, `OverrideInvalidated`, `OverrideRevoked`, `PlanApproved`, `SimulatedDispatchSent`.

`affects_planning: false` — `EscalatedToHuman`, `DuplicateCandidateFlagged`, `PlanProposed`, `PlanSuperseded`, `PlanFailed`, `ApprovalRejected`, `OverrideRejected`, `SimulatedDispatchQueued`, `MedicalProfileAccessGranted`, `MedicalProfileAccessDenied`, `HospitalPreAlertSimulated`, `ModelAdapterDegraded`.

Unit position ticks from the simulator are coalesced to at most one `UnitPositionUpdated` per unit per 10 simulated seconds so an approval is not invalidated by every movement tick. A position update only affects planning because ETAs and locks depend on it.

### Privacy in events

Payloads hold IDs, enums, numbers, coordinates and evidence span offsets. Caller free text is written to a separate `report_text` store keyed by `report_id` (revocable, excluded from exported event logs); the event carries `text_sha256` and length. Medical profiles live in a separate profile store; access events list field *names* read, never values.

## Plan lifecycle

```
computing ─► proposed ─► approved ─► dispatching ─► dispatched_simulated
                │  │                     │
                │  └► superseded         └► dispatch_partial_failed
                └► failed
```

- `proposed`: the only approvable state. Carries `plan_id`, `version`, `based_on_planning_sequence`, `policy_version`, `assignments[]`, `unmet_needs[]`, `flags[]`, `diff` versus the current approved plan, `solver{status, objective, wall_time_ms}`.
- A new planning-relevant event makes every `proposed` plan with an older `based_on_planning_sequence` **stale**. The server appends `PlanSuperseded` once the next proposal exists; until then the UI shows "Stale — recomputing" and approval is rejected.
- Recompute runs automatically after planning-relevant events (debounced so one scenario step yields one proposal) and on `POST /plans/recompute`. A recompute whose assignments and unmet needs equal the approved plan's appends no `PlanProposed`; the UI shows "Approved plan is current".
- `approved` does not mean vehicles moved. Only `SimulatedDispatchSent` for an assignment changes that unit to `en_route` in the projection.
- The previously approved plan remains the operating plan until a new one is approved. A failed or unapproved proposal never changes unit tasks.

## Approval (atomic check-and-append)

`POST /plans/{plan_id}/approve`

```json
{
  "expected_plan_version": 7,
  "expected_planning_sequence": 58,
  "acknowledged_flag_ids": ["flag_0007_1", "flag_0007_2"],
  "note": "ALS shortage acknowledged; requesting mutual aid outside simulation."
}
```

In one SQLite `BEGIN IMMEDIATE` transaction:

1. Plan exists → else `404`.
2. Plan state is `proposed` → else `409 PLAN_NOT_PROPOSED`.
3. `expected_plan_version == plan.version` and `expected_planning_sequence == plan.based_on_planning_sequence == current planning_sequence` → else `409 STALE_PLAN` with `current`.
4. Every flag with `requires_ack` is in `acknowledged_flag_ids` → else `409 UNACKNOWLEDGED_FLAGS`.
5. Re-validate H1–H8 against current state (defence in depth).
6. Append `PlanApproved` and one `SimulatedDispatchQueued` per new/changed assignment (outbox key `plan_id:assignment_id`), commit.

Rejections at step 2–5 append `ApprovalRejected{plan_id, code}` for audit (non-planning). Two operators approving the same version: the first commits; the second sees `PLAN_NOT_PROPOSED`. An approval racing a breakdown event: whichever commits first wins; if the breakdown commits first, approval is `STALE_PLAN`; if the approval commits first, the breakdown then invalidates the affected assignment and triggers a new proposal.

Whole-plan approval only in the MVP. Per-assignment choices are expressed through overrides (0004). No automatic approval exists in the MVP; every dispatch is operator-approved.

## Simulated dispatch outbox

- A worker reads undelivered `SimulatedDispatchQueued` rows, calls the **simulated** sender (in-process; no network, SMS, radio or phone), and appends `SimulatedDispatchSent{outbox_key}` with idempotency key = outbox key. A duplicate delivery attempt finds the key and appends nothing.
- `HospitalPreAlertSimulated` follows the same pattern.
- Every UI label and event name says "simulated". There is no configuration that enables a real transport.

## Replay

- Projection is a pure function of the ordered events: `state = fold(apply, events[1..n])`. Replaying events 1..n on an empty store must produce a state hash equal to the live projection hash at `n` (CC-03 test).
- Replay never runs the outbox sender, solver, route provider or model adapters. It reads their recorded results from events.
- UI replay mode (0006) requests `GET /state?at_sequence=n` (or folds events client-side from a snapshot); it is read-only and cannot issue commands.

## Snapshot, event feed and WebSocket

- `GET /state` returns `{schema_version, session_id, as_of_sequence, planning_sequence, sim_time_s, incidents, units, facilities, flood, active_overrides, approved_plan, current_proposal}`.
- `GET /events?after_sequence=n&limit=500` returns ordered envelopes; `410 SNAPSHOT_REQUIRED` if `n` is outside retained history or from another session.
- WebSocket `/ws/events`:
  1. Server → `{"type": "hello", "session_id", "head_sequence", "schema_version"}`.
  2. Client → `{"type": "subscribe", "session_id", "after_sequence": n}`.
  3. Server → backlog then live `{"type": "event", "event": <envelope>}` in order, or `{"type": "snapshot_required"}`.
  4. Server → `{"type": "heartbeat", "head_sequence"}` every 10 s.
- Client rule: apply only `sequence == last + 1`; on a gap, duplicate-ahead or `session_id` change, stop applying, fetch `GET /state`, resubscribe from `as_of_sequence`. Duplicates (`sequence ≤ last`) are ignored. No message for 30 s → UI `disconnected`; reconnect with backoff 1, 2, 4, 8 s (max 8 s).
