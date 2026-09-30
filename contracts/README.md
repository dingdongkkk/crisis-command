# Contract gate (CC-01 drafts; CC-02 implements)

Agree on canonical Pydantic models, JSON Schema/OpenAPI export and generated TypeScript types. Do not hand-maintain competing definitions.

Minimum entities: Incident, Report, TriageFacts, Unit, Hospital, Shelter, FloodZone, Route, Assignment, Plan, PlanDiff, PolicyFlag, Override, EventEnvelope, MedicalProfileConsent.

Define enums, optional vs unknown, timestamp format, sequence/version, `[longitude, latitude]` GeoJSON order, seconds/metres for routing, population/capacity units, errors and schema versioning.

Proposed API surface to finalize:

- `GET /health`, `GET /state`, `GET /events?after_sequence=...`
- `POST /reports`, `POST /units/{id}/status`, `POST /flood-events`
- `POST /plans/recompute`, `GET /plans/{id}`
- `POST /plans/{id}/approve`, `POST /overrides` with expected plan/event version
- `POST /demo/reset`, `POST /demo/advance` (simulation mode only)
- WebSocket `/ws/events`: envelope type, snapshot/reconnect/sequence semantics

Publish success and invalid examples for each command. Include idempotency, unauthorized profile access and stale approval errors. UI mocks must validate against the same generated schemas as the backend.
