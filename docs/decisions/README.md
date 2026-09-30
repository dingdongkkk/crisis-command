# CC-01 decision records

Accepted by CC-01 (Claude Opus 5.5) pending Codex feasibility review. These records are the specification CC-02 onward implements. A later task changes a decision by adding a new record that says which one it supersedes; do not silently edit accepted numbers or semantics in code.

| ID | Decision | Primary consumers |
| --- | --- | --- |
| [0001](0001-contract-conventions.md) | Coordinates, time, units, IDs, schema versions, errors, idempotency | CC-02, all |
| [0002](0002-triage-unknowns-and-escalation.md) | Tri-state facts, `unknown` handling, question policy, human handoff | CC-05, CC-06 |
| [0003](0003-allocation-objective-als-and-reserve.md) | Hard/soft constraints, objective bounds, ALS shortage, BLS bridge, reserve coverage | CC-05, CC-08 |
| [0004](0004-overrides-and-conflicts.md) | Override kinds, conflict detection, recording rejected overrides | CC-05, CC-08 |
| [0005](0005-plan-lifecycle-approval-and-replay.md) | Plan versions, stale approval, simulated dispatch outbox, replay, reconnect | CC-03, CC-08, CC-09 |
| [0006](0006-operator-screen-states.md) | Operator console and intake screen states | CC-04, CC-09 |
| [0007](0007-acceptance-scenarios.md) | Demo fixture and Given/When/Then acceptance scenarios | CC-03 to CC-11 |
| [0008](0008-contract-examples.md) | Entity, event and API examples (valid and invalid) | CC-02, CC-04 |

Machine-readable examples live in [examples/](examples/). CC-02 moves them into `contracts/` as canonical contract-test fixtures and generates schemas from Pydantic models; after that, `contracts/` is the source of truth and these files are historical.

## Numbers in these records

Every numeric policy value (lock threshold, penalty weights, question limits, coverage radius) is a **demonstration default**, not a clinical or operational standard. Each is carried in a versioned policy object (`policy_version`) so plans and events record which values produced them. None is derived from medical evidence; the brief's 20% example is deliberately not used as a threshold.
