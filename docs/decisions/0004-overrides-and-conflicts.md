# 0004 — Operator overrides and conflicts

Status: accepted (CC-01). Consumers: CC-05, CC-08, CC-04/CC-09 override dialog.

## Decision

Overrides are operator **constraints on future planning**, not direct edits of a plan. An accepted override causes a recompute; the operator then approves the resulting plan like any other. Overrides never bypass hard constraints H1–H7 (0003).

### Kinds

| `kind` | Fields | Effect on solver |
| --- | --- | --- |
| `pin` | `unit_id`, `need_id` | Unit must serve need (H8). |
| `forbid` | `unit_id`, `incident_id` | Unit may not serve incident. |
| `hold_unit` | `unit_id`, `zone_id?` | Unit gets no task (hard reserve chosen by a human). |
| `approve_bls_bridge` | `unit_id`, `bridges_need_id` | Adds a bridge task (0003). |
| `downgrade_need` | `need_id`, `reason_text` | Removes a provisional need from allocation; original need event retained. |
| `revoke` | `override_id` | Ends an active override. |

Every override body carries `expected_plan_id`, `expected_planning_sequence`, `reason_text` (≤ 280 chars, no medical detail beyond need type) and requires `Idempotency-Key`.

### Validation order (single transaction)

1. `expected_planning_sequence` must equal current `planning_sequence`, else `409 STALE_PLAN` (the operator was looking at an old world). Stale overrides are recorded as `OverrideRejected{reason: "STALE"}`.
2. Structural checks: IDs exist, need/unit types compatible.
3. Hard-constraint checks against current state plus all **active** overrides:

| Conflict code | Example |
| --- | --- |
| `UNIT_NOT_AVAILABLE` | pin `unit_A2` while `broken_down` |
| `UNIT_LOCKED` | pin `unit_A1` elsewhere while `on_scene` at `inc_0001` |
| `TYPE_INELIGIBLE` | pin a BLS unit to an ALS need (use `approve_bls_bridge`) |
| `ROUTE_UNAVAILABLE` | pin a road unit to an incident inside a closed flood polygon |
| `CAPACITY_EXCEEDED` | pin exceeds boat seats or shelter places |
| `DUPLICATE_UNIT_PIN` | second active pin/bridge/hold for the same unit |
| `CONTRADICTS_OVERRIDE` | `pin` A to X while an active `forbid` A from X, or `hold_unit` A |

4. If any conflict: respond `409 OVERRIDE_CONFLICT` with `conflicts[]` (`code`, `override_id?`, `unit_id`, `detail`) and append `OverrideRejected` with the same conflicts. **Nothing about the plan changes.** The rejected attempt is kept in the audit log and shown in the override panel history.
5. Otherwise append `OverrideAccepted`, then trigger recompute. The new proposal lists `soft_consequences[]` of the override versus the plan without it: `{metric: "weighted_eta_s", delta: 212}`, `{metric: "reserve_uncovered", zone_id: "zone_north"}`, `{metric: "unmet_need", need_id: …}`. If the override causes another need to become unmet, flag `OVERRIDE_CAUSES_UNMET` (`requires_ack`).

The operator replaces an active override only by `revoke` then a new override, or a single request with `replaces_override_id`, which is validated as if the replaced override were already revoked.

### Invalidation

When later world events make an active override violate H1–H7 (pinned unit breaks down, flood cuts the route, incident resolved), the server appends `OverrideInvalidated{override_id, reason}`, removes it from solver input, and the next plan carries flag `OVERRIDE_INVALIDATED` (`requires_ack`). An override is never silently kept in breach, and the plan is never made invalid to honour it.

## Rejected alternatives

- Let operators drag assignments into a plan and approve directly — bypasses the invariant gate and creates unversioned plans.
- Accept infeasible overrides and mark the plan "infeasible" — produces an invalid plan the UI might present as approvable.
- Drop conflicting overrides silently — hides operator intent; the invariant requires recording them.
