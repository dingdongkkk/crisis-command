# 0008 — Contract examples

Status: accepted (CC-01) as draft fixtures, revised after Codex review — see [0009](0009-review-resolutions.md). CC-02 turns each into a contract test against the canonical Pydantic models, then moves them under `contracts/`. Until then, `scripts/contract_fixture_checks.py` and `tests/test_cc01_contracts.py` check cross-file consistency (they are fixture checks, not the application schema).

| File | Contents | CC-02 test expectation |
| --- | --- | --- |
| [examples/policy.valid.json](examples/policy.valid.json) | Policy `demo-2026.2`: fact polarity, objective tiers, weights, caps, declared limits, tick/debounce/solver budget, lock threshold | loads into the versioned policy model |
| [examples/world.before.json](examples/world.before.json) | Consistent snapshot checkpoint at sequence 52 (session `sess_demo_01`), with embedded approved plan v6, outbox and historical plans | validates; checkpoint + events 53–67 folds to the same state as replay from sequence 1 |
| [examples/entities.valid.json](examples/entities.valid.json) | Report, complete TriageFacts, Incident, Unit, Hospital, Shelter, FloodZone, ReserveZone, Route (ok and unavailable), bridge Assignment, Override, MedicalProfileConsent | each validates |
| [examples/plan.valid.json](examples/plan.valid.json) | T+10 proposal v7: locked units, two unmet critical ALS quanta, provisional and reserve flags, coverage, embedded routes, diff, bridge candidates, `objective_vector` | validates; passes H1–H8; objective vector recomputes from the plan |
| [examples/events.valid.json](examples/events.valid.json) | Complete contiguous suffix 53–67: report, triage, incident, assessment, escalation, breakdown, proposal (full embedded plan), rejected override, approval, three queued and three sent session-qualified dispatch commands | validate; approval binds to planning sequence 58 while 59–60 are non-planning; planning sequence ends at 67 |
| [examples/api.examples.json](examples/api.examples.json) | 26 request/response cases; every POST carries `expected_session_id`. Includes idempotent retry, key reuse, wrong session, reset retry, stale approval, missing ack, override conflict, geographically valid report outside the demo box, profile denial, simulation-only | valid bodies validate; invalid ones produce the listed problem `code`; snapshot and `GET /plans/{id}` embed exactly `plan.valid.json` |
| [examples/schema.invalid.json](examples/schema.invalid.json) | 16 negative cases, each a valid base (file + JSON pointer) plus RFC 6902 patches, with `expected_error` and `validation_layer` (`schema`, `fixture` or `domain`) | the unpatched base passes; the patched value fails with exactly the named error |

ETAs and objective values are synthetic fixture values consistent with the 0003 policy; they are not claims about real Bengaluru travel times.

## Final API surface (v1.0)

| Method & path | Purpose | Idempotency key | Notes |
| --- | --- | --- | --- |
| `GET /health` | liveness + mode + providers + degraded causes | — | |
| `GET /state[?at_sequence=n&session_id=s]` | snapshot with embedded `approved_plan`/`current_proposal`; replay requires the session | — | 0005 |
| `GET /events?after_sequence=n&session_id=s[&limit=]` | ordered envelopes | — | session required; `410 SNAPSHOT_REQUIRED` |
| `POST /reports` | synthetic caller text/structured answers | required | creates/links incident, runs intake |
| `POST /reports/{id}/answers` | structured answer to the pending question | required | `{fact_key, answer}` with answer `yes`, `no` or `unknown` |
| `POST /incidents/{id}/facts/{key}/confirm` | operator confirms a fact | required | `TriageFactConfirmed` |
| `POST /incidents/{id}/duplicates/{report_id}/resolve` | operator links or keeps separate | required | never automatic |
| `POST /incidents/{id}/medical-profile-access` | consented synthetic profile read | required | 403 reasons below |
| `POST /units/{id}/status` | simulated unit status | required | |
| `POST /flood-events` | new flood zone version | required | |
| `POST /plans/recompute` | request recompute | required | `202` |
| `GET /plans/{id}` | plan envelope | — | |
| `POST /plans/{id}/approve` | whole-plan approval | required | 0005 |
| `POST /overrides` | pin/forbid/hold/bridge/downgrade/revoke | required | 0004 |
| `POST /demo/reset`, `POST /demo/advance` | simulation control | required | `403 SIMULATION_ONLY` outside simulation; reset receipts survive resets (0001) |
| `WS /ws/events` | hello/subscribe/event/heartbeat/snapshot_required | — | 0005 |

Every mutating body includes `expected_session_id` (else `409 STALE_SESSION`); approvals and overrides also carry the expected plan and planning sequence. Lock contention returns `503 DATABASE_BUSY`; retry with the same key.

`PROFILE_ACCESS_DENIED` reasons: `NO_CONSENT`, `CONSENT_REVOKED`, `CALLER_IS_NOT_PATIENT`, `CALLER_IS_PATIENT_UNKNOWN`, `INCIDENT_NOT_ACTIVE`, `PROFILE_NOT_LINKED`, `MISSING_OPERATOR_REASON`. `caller_is_patient` is a triage fact; `unknown` denies access.

No endpoint sends a real call, SMS, radio message, emergency-service request or family notification. There is no authentication in the MVP demo; `actor.id` is a configured synthetic operator. That is a stated limitation, not a security control.
