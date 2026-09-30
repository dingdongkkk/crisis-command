# 0003 — Allocation constraints, objective bounds, ALS shortage and reserve coverage

Status: accepted (CC-01). Consumers: CC-05 solver, CC-07 routing inputs, CC-08 policy gate, UI flags.

## Hard constraints (never violated by any plan, fallback or override)

| ID | Constraint |
| --- | --- |
| H1 | Unit exists in the fleet for this session. |
| H2 | Unit `status` is `available` or `returning`, or assigned-but-unlocked (`en_route` outside lock threshold). `out_of_service`, `broken_down`, `off_duty` units have no assignment; their previous assignments are invalidated. |
| H3 | Resource type is eligible (table below). |
| H4 | At most one active task per unit (no double-booking). |
| H5 | A route with `route_status: "ok"` exists from the unit's position to the incident and, for transport needs, onward to the chosen facility, under the current flood version. Unknown or failed routes are ineligible (`ROUTE_UNAVAILABLE`), never straight-line estimates. |
| H6 | Facility capacity: assigned shelter persons ≤ `capacity_persons − occupied_persons`; hospital destinations ≤ `ed_beds_available`; boat persons ≤ `capacity_persons`. |
| H7 | Locked units keep their current task. Lock = status `on_scene` or `transporting`, or `en_route` with remaining route time ≤ **120 s** (`near_arrival_lock_s`). |
| H8 | Accepted operator pins/forbids/holds (0004). |

### Eligibility

| Need type | Eligible unit types | Note |
| --- | --- | --- |
| `als` | `als` | BLS is never eligible and never relabelled. |
| `bls` | `bls`, `als` | ALS on a BLS need costs `als_on_bls_cost` (soft). |
| `fire` | `fire` | |
| `water_rescue` | `boat` | |
| `tow` | `tow` | Only for `emergency` category (e.g. flood-stranded vehicle). |
| `shelter_places` | facility, not a unit | Allocated as persons to a shelter, H6. |

## Objective (minimise, integers only)

```
total = Σ unmet_need_cost(need)
      + Σ travel_cost(assignment)
      + Σ reassignment_cost(moved unit)
      + Σ reserve_shortfall_cost(zone, type)
      + Σ als_on_bls_cost(assignment)
```

Default `demo-2026.1` weights:

| Term | Value |
| --- | --- |
| Severity weight `w` | critical 5, high 3, medium 2, low 1 |
| `travel_cost` | `w × min(eta_s, 3600)` |
| `unmet_need_cost` | critical 20 000 000; high 300 000; medium 60 000; low 15 000; plus `w × min(waiting_s, 3600)` |
| `reassignment_cost` | 600 per non-locked unit whose target changes from the currently approved plan |
| `reserve_shortfall_cost` | 900 per (zone, required type) left uncovered |
| `als_on_bls_cost` | 900 per ALS unit on a BLS-only need |

### Bounds that must hold (CC-05 asserts them in a test against the declared scenario limit)

Declared limit: ≤ 25 units, ≤ 30 needs, ≤ 6 reserve zones × 2 types.

1. One critical unmet need outweighs every non-critical term combined at the declared limit: `20 000 000 > 30 × (300 000 + 5 × 3600) + 25 × (5 × 3600) + 25 × 600 + 12 × 900 + 25 × 900` (= 10 038 300: all other needs unmet at high with maximum waiting, plus maximum travel, reassignment, reserve and waste). So the solver never leaves a critical need unmet to reduce travel, reassignment, reserve or waste.
2. Any unmet high need outweighs any single assignment's travel: `300 000 > 5 × 3600`.
3. Reserve shortfall (900) is less than the lowest unmet cost (15 000): **the solver never withholds a unit from a need to keep reserve.** It only uses reserve to break travel trade-offs: at critical weight, it accepts at most 180 s extra ETA to keep a zone covered; at low weight, 900 s.
4. Reassignment (600) means moving an en-route unlocked unit must save more than 120 s of critical-weighted travel.

Changing a weight requires a new `policy_version` and rerunning the bound test.

### Determinism

Fixed `num_search_workers = 1`, fixed random seed, time limit 2 s per solve (demo default), stable ordering of units and needs by ID. Equal-cost ties break on lowest unit ID then lowest need ID via a tiny lexicographic tiebreak term below 1 objective unit (scale all other terms × 1000 internally if needed). Record `solver_status`, `objective`, `wall_time_ms` in the plan.

### Solver outcomes

| Status | Plan result |
| --- | --- |
| `OPTIMAL` | proposal |
| `FEASIBLE` (time limit) | proposal with flag `SOLVER_TIME_LIMIT` (info) |
| `INFEASIBLE`/`UNKNOWN`/error | deterministic greedy fallback (nearest eligible reachable, severity order), re-validated against H1–H8, flag `FALLBACK_HEURISTIC` (`requires_ack`) |
| Fallback fails validation | `failed` plan with `NO_VALID_PLAN`; the last approved plan stays in force and the UI says so |

Unmet demand is a decision variable, so infeasibility should only arise from contradictory operator constraints, which 0004 rejects before solving.

## ALS shortage

- An ALS need with no eligible, available, reachable ALS stays in `plan.unmet_needs` with reason codes, e.g. `NO_ALS_AVAILABLE`, `ALS_LOCKED_ON_SCENE` (with unit IDs), `ALS_OUT_OF_SERVICE`, `ALS_UNREACHABLE`.
- Plan flag `ALS_UNMET` (severity `critical`, `requires_ack: true`) per affected incident. Approval requires acknowledging it (0005). Acknowledgement records that the operator saw the shortage; it does not mark the need met.
- The unmet ALS need persists and is re-solved on every replan. When an ALS unit becomes available, the next plan assigns it if eligible.
- `unmet_needs[].bridge_candidates` lists up to 3 reachable BLS units ordered by ETA, with ETA and the cost of taking each (which need/zone it leaves).

### BLS bridge

- The solver **never** assigns a bridge on its own. The operator creates an `approve_bls_bridge` override (0004) naming the BLS unit and the unmet ALS need.
- A bridge assignment has `role: "bridge"`, `satisfies_need: false`, `bridges_need_id`. It occupies the BLS unit (H4) but does not reduce ALS unmet cost, so the `ALS_UNMET` flag remains, relabelled `ALS_UNMET_BLS_BRIDGING` (still `critical`, still `requires_ack`).
- If the BLS unit's own BLS need elsewhere becomes unmet as a result, that shows as its own unmet need and flag.
- UI copy: "BLS bridge — not ALS care. ALS still unmet."

## Reserve coverage (soft)

- Fixture defines reserve zones (polygon + required types + `coverage_eta_s`, default 600 s). A zone/type is covered if at least one `available` (unassigned after this plan) unit of that type, or a superset type, has a route to the zone's reference point within `coverage_eta_s`.
- Coverage is a **soft** term. It is never hard, because a hard reserve could force a critical need to be unmet, contradicting bound 1. The brief's "absolute" reserve wording is satisfied only by an explicit operator `hold_unit` override, which then becomes H8 and shows its own consequences.
- Each uncovered zone/type yields flag `RESERVE_UNCOVERED` (severity `warning`, `requires_ack: true`) with `zone_id`, `resource_type`, and `since_sim_time_s`.
- Coverage is computed from the plan's resulting positions, using the same route provider and flood version as allocation. Routing failure for coverage marks the zone `coverage_unknown` (flag `RESERVE_COVERAGE_UNKNOWN`), not covered.

## Reason facts

Every assignment and unmet need carries `reasons[]` of `{code, params}` from a closed catalog, used for "why" and "why not" (e.g. `NEAREST_ELIGIBLE`, `ETA_WORSE_BY {unit_id, delta_s}`, `UNIT_LOCKED {unit_id, lock}`, `TYPE_INELIGIBLE`, `ROUTE_UNAVAILABLE {unit_id, flood_version}`, `KEPT_FOR_RESERVE {zone_id}`, `CAPACITY_EXCEEDED {facility_id}`, `OVERRIDE_PIN {override_id}`). Template or model explanations are generated only from these; numbers in explanations must match these params.

## Flag catalog (v1.0)

| Code | Severity | `requires_ack` | Raised when |
| --- | --- | --- | --- |
| `ALS_UNMET` | critical | yes | ALS need unmet, no bridge |
| `ALS_UNMET_BLS_BRIDGING` | critical | yes | ALS need unmet, operator bridge active |
| `CRITICAL_NEED_UNMET` | critical | yes | any other critical-severity need unmet |
| `NEED_UNMET` | warning | yes | non-critical need unmet |
| `RESERVE_UNCOVERED` | warning | yes | zone/type without coverage after plan |
| `RESERVE_COVERAGE_UNKNOWN` | warning | yes | coverage routing failed |
| `OVERRIDE_CAUSES_UNMET` | warning | yes | accepted override makes another need unmet |
| `OVERRIDE_INVALIDATED` | warning | yes | active override removed by world change |
| `FALLBACK_HEURISTIC` | warning | yes | greedy fallback used |
| `PROVISIONAL_NEED` | info | no | need based on `unknown` critical facts |
| `SOLVER_TIME_LIMIT` | info | no | feasible, not proven optimal |
| `ROUTING_DEGRADED` | warning | yes | route provider failed for some pairs; those pairs ineligible |

Flag IDs are `flag_<plan version>_<n>` and are unique per plan; acknowledgements bind to the plan version, so a new plan needs fresh acknowledgements.
