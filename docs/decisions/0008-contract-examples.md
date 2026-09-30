# 0008 — Contract examples

Status: accepted (CC-01) as draft fixtures. CC-02 turns each into a contract test against the canonical Pydantic models, then moves them under `contracts/`.

| File | Contents | CC-02 test expectation |
| --- | --- | --- |
| [examples/entities.valid.json](examples/entities.valid.json) | Report, TriageFacts, Incident, Unit, Hospital, Shelter, FloodZone, ReserveZone, Route (ok and unavailable), Override, MedicalProfileConsent | each validates |
| [examples/plan.valid.json](examples/plan.valid.json) | T+10 proposal: locked units, unmet ALS, reserve flags, diff, bridge candidates, solver status | validates; passes H1–H8 validator against the fixture |
| [examples/events.valid.json](examples/events.valid.json) | Excerpt of envelopes 53–65: report, breakdown, proposal, rejected override, approval, outbox queue/sent. Elided: 54–57 intake for rpt_0010 (`TriageFactsExtracted`, `IncidentCreated`, `IncidentAssessed`, planning; `EscalatedToHuman`, non-planning) and 63–64 (remaining `SimulatedDispatchQueued`); 66–67 are the other `SimulatedDispatchSent` events | validate; sequences strictly increasing; approval binds to planning sequence 58 while 59–60 are non-planning |
| [examples/api.examples.json](examples/api.examples.json) | Request/response pairs for every endpoint, including idempotent retry, key reuse, stale approval, missing ack, override conflict, profile denial, simulation-only | request bodies validate (valid cases) or produce the listed problem `code` |
| [examples/schema.invalid.json](examples/schema.invalid.json) | Swapped/lat-lng coordinates, non-UTC time, fractional ETA, boolean facts, unknown-as-zero, evidence-less negatives, bridge satisfying need, double booking, unreachable assignment, raw text in event | each fails schema or plan validation with the stated reason |

The example ETAs and objective values are placeholders consistent with the 0003 weights; they are not claims about real Bengaluru travel times.

## Final API surface (v1.0)

| Method & path | Purpose | Idempotency key | Notes |
| --- | --- | --- | --- |
| `GET /health` | liveness + mode + providers + degraded causes | — | |
| `GET /state[?at_sequence=n]` | snapshot; `at_sequence` for replay | — | 0005 |
| `GET /events?after_sequence=n[&session_id=][&limit=]` | ordered envelopes | — | `410 SNAPSHOT_REQUIRED` |
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
| `POST /demo/reset`, `POST /demo/advance` | simulation control | required | `403 SIMULATION_ONLY` outside simulation |
| `WS /ws/events` | hello/subscribe/event/heartbeat/snapshot_required | — | 0005 |

`PROFILE_ACCESS_DENIED` reasons: `NO_CONSENT`, `CONSENT_REVOKED`, `CALLER_IS_NOT_PATIENT`, `CALLER_IS_PATIENT_UNKNOWN`, `INCIDENT_NOT_ACTIVE`, `PROFILE_NOT_LINKED`, `MISSING_OPERATOR_REASON`. `caller_is_patient` is a triage fact; `unknown` denies access.

No endpoint sends a real call, SMS, radio message, emergency-service request or family notification. There is no authentication in the MVP demo; `actor.id` is a configured synthetic operator. That is a stated limitation, not a security control.
