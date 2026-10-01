# Contracts (CC-01 specified; CC-02 implemented)

Canonical Pydantic models in `backend/app/contracts/` are the single definition. Everything else is generated:

```
backend/app/contracts/*.py
  └─ uv run python -m app.contracts.export  → contracts/schema/crisis-command.schema.json, contracts/openapi.json
       └─ npm run gen:contracts             → frontend/src/generated/contracts.ts
```

CI fails if either generated artifact is stale. UI mocks validate at runtime against the same JSON Schema (`frontend/src/contracts.ts`, AJV draft 2020-12). Contract tests (`backend/tests/test_contracts.py`, `frontend/src/contracts.test.ts`) validate every CC-01 example and require each negative case to fail with its named error code. Examples still live in `docs/decisions/examples/` until CC-01 merges; move them here afterwards without changing content.

## Specification

| Topic | Decision record |
| --- | --- |
| `[longitude, latitude]` GeoJSON, RFC 3339 UTC `Z` times, `sim_time_s`, integer seconds/metres/persons/beds, IDs, schema versioning, problem+json errors, idempotency | [0001](../docs/decisions/0001-contract-conventions.md) |
| Tri-state `TriageFacts` with evidence; `unknown` versus omitted | [0002](../docs/decisions/0002-triage-unknowns-and-escalation.md) |
| `Assignment`, `Plan`, unmet needs, `PolicyFlag`, reason facts, bridges | [0003](../docs/decisions/0003-allocation-objective-als-and-reserve.md) |
| `Override` kinds and conflict codes | [0004](../docs/decisions/0004-overrides-and-conflicts.md) |
| `EventEnvelope`, event catalog, planning sequence, approval, outbox, WebSocket | [0005](../docs/decisions/0005-plan-lifecycle-approval-and-replay.md) |
| Final API surface and valid/invalid examples | [0008](../docs/decisions/0008-contract-examples.md) |

Entities: Report, TriageFacts, Incident (with needs), Unit, Hospital, Shelter, FloodZone, ReserveZone, Route, Assignment, FacilityAllocation, Plan, PlanDiff, PolicyFlag, Override, EventEnvelope, MedicalProfileConsent. Initial `schema_version` is `"1.0"`.

## Rules for changes

Codex is integration owner after CC-01. A change needs valid and invalid examples, an explicit MAJOR/MINOR version impact (0001) and updates to both backend and frontend consumers in the same PR. A change to the meaning of a field, a constraint or approval semantics also needs a new decision record superseding the old one. Domain rules and route units must not be inferred from screen labels.
