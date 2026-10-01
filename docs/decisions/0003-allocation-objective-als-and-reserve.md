# 0003 — Allocation constraints, objective bounds, ALS shortage and reserve coverage

Status: accepted (CC-01), revised after Codex review — see [0009](0009-review-resolutions.md). Consumers: CC-05 solver, CC-07 routing inputs, CC-08 policy gate, UI flags.

## Hard constraints (never violated by any plan, fallback or override)

| ID | Constraint |
| --- | --- |
| H1 | Unit exists in the fleet for this session. |
| H2 | For new/changed tasks, unit `status` is `available` or `returning`, or assigned-but-unlocked (`en_route` outside lock threshold). Existing locked tasks are retained under H7. `out_of_service`, `broken_down`, `off_duty` units have no assignment; their previous assignments are invalidated. |
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

## Objective (lexicographic, integers only)

Policy `demo-2026.2` replaces the original scalar penalty claim. Minimise in order:

```
(unmet_critical, unmet_high, unmet_medium, unmet_low, waiting_cost, operating_cost)
```

Each `unmet_<severity>` is the sum of `quantity_unmet` in that severity. A quantity is a declared demand quantum: one ALS/BLS/fire/tow/boat unit slot, or one shelter person. A boat's passenger capacity is a separate hard check; it cannot satisfy a rescue of unknown size without a flagged explicit planning assumption. Partial fulfilment reduces missing quanta; never charge one flat penalty for an entire partially met need record.

`waiting_cost = Σ quantity_unmet × w × min(waiting_s, 3600)`, with critical/high/medium/low `w = 5/3/2/1`. This prefers older needs within a fixed fulfilled-count vector. Quantity comparisons across different need types are an explicit demo simplification.

`operating_cost` is the sum of:

| Term | Value |
| --- | --- |
| travel | `w × min(eta_s, 3600)` per unit assignment |
| reassignment | 600 per unlocked unit changing an existing approved task; newly assigned idle units are not reassignments |
| reserve shortfall | 900 per uncovered (zone, required type) |
| ALS on BLS | 900 per ALS unit serving a BLS-only need |

### Bounds and guarantees

Declared limits: ≤25 units, ≤30 need records, ≤2000 total demand quanta, ≤6 zones ×2 reserve types. Reject a fixture exceeding these limits. The maximum operating cost is `25×5×3600 + 25×600 + 12×900 + 25×900 = 498300`. Maximum waiting cost is `2000×5×3600 = 36000000`. These bounds check integer domains, not dominance via a scalar weight.

Solve lexicographic tiers in separate passes, fixing a tier's value only after it is proven optimal. Never start waiting/operating optimisation until all unmet-count tiers are proven optimal. Thus **reserve cannot cause extra unmet demand at any severity while higher tiers stay equal**. Under scarcity, meeting a higher tier may still increase lower-tier unmet demand; no claim says every need is always satisfiable. The review counter-example (one ALS covers 12 reserve pairs, low BLS at 3600 s) must select service: its unmet-low count is 0 versus 1, regardless of the 15300 operating cost.

A timeout at any pass returns its feasible incumbent with `lexicographic_complete: false`, `completed_tiers` and `SOLVER_TIME_LIMIT`; it is not labelled lexicographically optimal. Do not run lower passes after an unproven higher pass. Compare fallback candidate plans with the same tuple and enforce H1–H8. No guarantee of global optimality is claimed for a timed-out solve or fallback.

### Determinism

One worker, fixed seed, stable ordered input IDs and a total 2 s wall-time budget across all passes. After all six tiers are proven, an optional deterministic tie pass fixes each unit's target in ID order; never perturb higher objectives with an unbounded summed tie term. If budget is exhausted, keep the last valid incumbent and record incomplete tie resolution. Pin the solver version; wall-time cutoffs can yield different feasible incumbents on different hardware, so exact-plan repeatability is asserted only for fixture runs completing every tier/tie pass. `solver` stores `objective_vector`, `completed_tiers`, `lexicographic_complete`, status, seed/workers and timing, not the superseded scalar `objective_cost`.

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
- `unmet_needs[].bridge_candidates` lists up to 3 reachable, available or unlocked BLS units ordered by ETA (exclude locked units, even at the same incident), with ETA and the cost of taking each (which need/zone it leaves).

### BLS bridge

- The solver **never** assigns a bridge on its own. The operator creates an `approve_bls_bridge` override (0004) naming the BLS unit and the unmet ALS need.
- A bridge assignment has `role: "bridge"`, `satisfies_need: false`, `bridges_need_id`. It occupies the BLS unit (H4) but does not reduce the ALS unmet-count tier, so the `ALS_UNMET` flag remains, relabelled `ALS_UNMET_BLS_BRIDGING` (still `critical`, still `requires_ack`).
- If the BLS unit's own BLS need elsewhere becomes unmet as a result, that shows as its own unmet need and flag.
- UI copy: "BLS bridge — not ALS care. ALS still unmet."

## Reserve coverage (soft)

- Fixture defines reserve zones (polygon + required types + `coverage_eta_s`, default 600 s). A zone/type is covered if at least one `available` (unassigned after this plan) unit of that type, or a superset type, has a route to the zone's reference point within `coverage_eta_s`.
- Coverage is a **soft** term. It is never hard, because a hard reserve could force a critical need to be unmet, contradicting the unmet-count priority. The brief's "absolute" reserve wording is satisfied only by an explicit operator `hold_unit` override, which then becomes H8 and shows its own consequences.
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
