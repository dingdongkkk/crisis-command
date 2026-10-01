# 0001 — Contract conventions

Status: accepted (CC-01), revised after Codex review — see [0009](0009-review-resolutions.md). Applies to every schema, event payload, API body and fixture.

## Geometry

- WGS 84, GeoJSON order **`[longitude, latitude]`**. A point is a GeoJSON `Point`; areas are `Polygon`/`MultiPolygon` with closed rings (first position repeated last), exterior counter-clockwise.
- Six decimal places at most (~0.1 m). Longitude in [-180, 180], latitude in [-90, 90]. The demo bounding box `[77.45, 12.80, 77.80, 13.15]` (Bengaluru) is enforced for fixtures only, not for the schema.
- A payload never carries `lat`/`lng` fields. `[12.97, 77.59]` (swapped) is an invalid example: it fails the demo bounding-box fixture check and must be caught by contract tests.

## Time

- Wall-clock instants: RFC 3339 UTC with `Z` and millisecond precision, e.g. `2026-09-30T09:15:02.120Z`. Offsets other than `Z` are rejected.
- Simulation clock: `sim_time_s`, integer seconds since scenario start. Every event and plan carries both. Solver inputs, waiting age and ETAs use **only** `sim_time_s`, so replays are deterministic regardless of wall clock.
- Ordering uses the global `sequence` (below), never timestamps.

## Quantities

| Quantity | Field suffix | Type | Notes |
| --- | --- | --- | --- |
| Duration / ETA | `_s` | integer seconds | `eta_s` ≥ 0; absent route is `null` with a reason, never an estimate |
| Distance | `_m` | integer metres | |
| People | `_persons` | integer ≥ 0 | shelter places, boat seats, people at incident |
| Beds | `_beds` | integer ≥ 0 | hospital emergency beds available |
| Penalty/objective | `_cost` | integer | solver objective units, see 0003 |

An unknown count (e.g. people trapped) is `{"value": null, "status": "unknown"}`, never `0` (see 0002).

## Identifiers

Opaque strings with a type prefix, stable across replay: `inc_0004`, `rpt_0007`, `unit_A2`, `hosp_H1`, `shelter_S1`, `zone_north`, `flood_bellandur`, `plan_0007`, `ovr_0002`, `need_0006_als`, `asg_…`. Event IDs are UUIDv4. `display_name` (e.g. `A2`) is presentation only; clients never parse IDs.

## Sequence and versions

- `sequence`: integer, starts at 1 per simulation `session_id`, strictly increasing by 1 with no gaps, assigned inside the append transaction.
- `session_id`: changes on `POST /demo/reset`. A client that sees a new `session_id` discards all local state and resyncs.
- `planning_sequence`: the sequence of the latest event whose catalog entry has `affects_planning: true`. Plans bind to it (0005).
- `plan.version`: integer, strictly increasing per session; each proposal gets a new version. `plan_id` is `plan_` + zero-padded version.
- `schema_version`: `"MAJOR.MINOR"` string in every envelope and snapshot. Additive optional fields bump MINOR; renames, removals, enum-value removals or semantic changes bump MAJOR. Consumers reject an unknown MAJOR and ignore unknown fields within a known MAJOR. Initial value `"1.0"`.
- `policy_version`: string (e.g. `"demo-2026.2"`) naming the rule/weight set used by assessment and solver.

## Idempotency

- Every mutating `POST` requires an `Idempotency-Key` header: a client-generated UUIDv4.
- Every mutating body also requires `expected_session_id`. The server creates an initial session on startup; clients obtain it through `/state`. A request targeting a different session is rejected with `409 STALE_SESSION` before any domain mutation. Plan versions and sequences alone never identify a session.
- Normal command receipts are keyed by `(expected_session_id, method, concrete path, key)` and retained for the lifetime of the persisted demo database, including across resets. A receipt contains the canonical request body/hash and original status/body. Never store profile values in receipts: profile-access responses contain an audited field-name grant, not profile contents.
- Inside the write transaction: look up the receipt first; if its body differs return `IDEMPOTENCY_KEY_REUSED`; if equal return the original response without applying anything. Only a new key proceeds to the expected-session check. Thus an old completed command may return its old receipt but cannot mutate a new session.
- Reset uses a database-wide receipt key `(POST, /demo/reset, key)` that survives reset. In one transaction validate the expected old session, cancel its pending deliveries, create a fresh session with `SessionStarted` sequence 1, switch the active session and save the receipt. A lost-response retry returns the same new session even after later resets; it never resets again. Different body with that key is rejected. Database deletion is the only receipt-retention boundary for this demo.
- Same key and byte-identical canonical JSON body → the server returns the **original** status code and body, appends nothing and sets `Idempotent-Replayed: true`.
- Same key with a different body → `422 IDEMPOTENCY_KEY_REUSED`, nothing appended.
- The key is stored in `EventEnvelope.idempotency_key` of the first event the command produced. System-generated events (watchdog, solver) use deterministic keys such as `watchdog:unit_A2:breakdown:600` so a re-run of the same scenario step cannot double-append.
- A command rejected for a business reason (stale plan, override conflict) is still idempotent: the retry returns the same rejection.

## Errors

RFC 9457 `application/problem+json`, with a stable machine `code` and optional `current` block describing the state the client should reload.

```json
{
  "type": "https://crisis-command.local/problems/stale-plan",
  "title": "Plan is no longer current",
  "status": 409,
  "code": "STALE_PLAN",
  "detail": "Plan plan_0007 was based on sequence 58; planning sequence is now 61.",
  "current": {"plan_id": "plan_0008", "plan_version": 8, "planning_sequence": 61}
}
```

| Code | HTTP | Meaning |
| --- | --- | --- |
| `VALIDATION_FAILED` | 422 | Schema violation; `errors[]` lists JSON pointers |
| `IDEMPOTENCY_KEY_MISSING` | 400 | Mutating request without key |
| `IDEMPOTENCY_KEY_REUSED` | 422 | Key reused with a different body |
| `STALE_SESSION` | 409 | Expected session differs from current; no domain event appended |
| `DATABASE_BUSY` | 503 | Writer lock could not be obtained within the bounded retry budget; retry same idempotency key |
| `NOT_FOUND` | 404 | Unknown ID |
| `STALE_PLAN` | 409 | Plan version or planning sequence is not current |
| `PLAN_NOT_PROPOSED` | 409 | Plan already approved, superseded, rejected or failed |
| `UNACKNOWLEDGED_FLAGS` | 409 | Approval omits a flag with `requires_ack: true`; `missing_flag_ids[]` |
| `OVERRIDE_CONFLICT` | 409 | Override violates a hard constraint; `conflicts[]` (0004) |
| `INVALID_TRANSITION` | 409 | e.g. status change for a unit that does not exist in that state |
| `PROFILE_ACCESS_DENIED` | 403 | Medical ID rule not satisfied; `reason` (0008) |
| `SIMULATION_ONLY` | 403 | `/demo/*` called when `CRISIS_MODE` is not `simulation` |
| `SNAPSHOT_REQUIRED` | 410 | `after_sequence` older than retained history or from another session |

## Enums

Initial v1.0 values:

| Enum | Values |
| --- | --- |
| `UnitType` | `als`, `bls`, `fire`, `boat`, `tow` |
| `UnitStatus` | `available`, `en_route`, `on_scene`, `transporting`, `at_facility`, `returning`, `broken_down`, `out_of_service`, `off_duty` |
| `NeedType` | `als`, `bls`, `fire`, `water_rescue`, `tow`, `shelter_places` |
| `Severity` | `critical`, `high`, `medium`, `low` |
| `IncidentCategory` | `emergency`, `non_emergency_assist`, `information_request` |
| `IncidentStatus` | `active`, `resolved`, `merged_duplicate` |
| `FactValue` | `yes`, `no`, `unknown` |
| `NeedBasis` | `confirmed`, `provisional_unknown` |
| `PlanState` | `computing`, `proposed`, `superseded`, `approved`, `dispatching`, `dispatched_simulated`, `dispatch_partial_failed`, `failed` |
| `RouteStatus` | `ok`, `unavailable`, `provider_error` |
| `AssignmentRole` | `primary`, `bridge` |
| `LockReason` | `on_scene`, `transporting`, `near_arrival` (or `null`) |
| `FlagSeverity` | `critical`, `warning`, `info` |
| `OverrideKind` | `pin`, `forbid`, `hold_unit`, `approve_bls_bridge`, `downgrade_need`, `revoke` |
| `OverrideStatus` | `active`, `rejected`, `invalidated`, `revoked` |

`available` and `returning` units are assignable; `en_route` units are assignable only outside the lock threshold; all other statuses cannot receive a new task. Existing on-scene/transporting/near-arrival assignments are retained under H7, not rejected by the new-assignment eligibility check.

Enum values are lower snake case strings, except solver statuses which mirror OR-Tools (`OPTIMAL`, `FEASIBLE`, …) and event/flag/reason codes which use their catalog spelling. Adding a value is a MINOR change only if consumers have an explicit fallback rendering; the UI must render an unknown enum as "Unrecognised (<value>)", never as a known state.

## Absent versus unknown

- A field that is not applicable is **omitted** (optional in the schema).
- A fact that applies but has not been established is **present with status `unknown`**.
- Nullable fields are explicit: `causation_id`, event `idempotency_key`, unit `current_task`, assignment `locked`, snapshot `approved_plan`/`current_proposal`, unknown count `value`, and unavailable route duration/distance/geometry. A missing task, lock, causal event or plan needs no artificial reason. An unavailable route requires `unavailable_reason`; an unknown count requires `status: unknown`.
- Model these as optional versus nullable deliberately in Pydantic, then export schema and generate TypeScript; a generated TypeScript type alone is not runtime validation. Normal incoming commands reject unexpected fields. Same-major event readers may ignore unknown additive fields, but event writers use closed payload models that forbid free-text/profile-value leakage.
