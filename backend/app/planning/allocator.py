"""Bounded lexicographic CP-SAT allocation with shared feasible greedy baseline.

Routes are inputs; neither this solver nor its fallback invents an ETA. All six
objective passes share one deadline. Lower tiers run only after optimality proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import monotonic
from typing import Any, Protocol

from ortools.sat.python import cp_model

from app.contracts.common import Point
from app.contracts.entities import Hospital, Incident, Need, Route, Shelter, Unit
from app.contracts.enums import ELIGIBLE_UNIT_TYPES, Severity
from app.contracts.plan import Plan
from app.contracts.state import StateSnapshot
from app.domain.commands import UNAVAILABLE, DomainError


class Routes(Protocol):
    def route(
        self, state: StateSnapshot, origin: tuple[float, float], destination: tuple[float, float]
    ) -> Route: ...


@dataclass
class Candidate:
    unit: Unit | None
    incident: Incident
    need: Need
    route: Route
    facility: str | None = None
    onward: Route | None = None
    capacity: int = 1
    lock: str | None = None
    bridge: bool = False
    persons: int | None = None


def lock_for(state: StateSnapshot, unit: Unit, route: Route | None = None) -> str | None:
    if unit.status in UNAVAILABLE or unit.current_task is None:
        return None
    if unit.status in ("on_scene", "transporting"):
        return unit.status.value
    if (
        unit.status == "en_route"
        and route
        and route.duration_s is not None
        and route.duration_s <= state.policy.near_arrival_lock_s
    ):
        return "near_arrival"
    return None


def _route(routes: Routes, state: StateSnapshot, a: Point, b: Point) -> Route:
    return routes.route(state, a.coordinates, b.coordinates)


def candidates(
    state: StateSnapshot, routes: Routes
) -> tuple[list[Candidate], dict[str, list[str]], bool]:
    out: list[Candidate] = []
    coverage: dict[str, list[str]] = {}
    degraded = False
    active = sorted(
        (i for i in state.incidents if i.status == "active"), key=lambda i: i.incident_id
    )
    for unit in sorted(state.units, key=lambda u: u.unit_id):
        if unit.status in UNAVAILABLE or unit.status == "at_facility":
            continue
        old = next(
            (
                a
                for a in (state.approved_plan.assignments if state.approved_plan else [])
                if unit.current_task and a.assignment_id == unit.current_task.assignment_id
            ),
            None,
        )
        current_inc = next((i for i in active if old and i.incident_id == old.incident_id), None)
        old_route = (
            _route(routes, state, unit.position, current_inc.location) if current_inc else None
        )
        lock = lock_for(state, unit, old_route)
        for inc in active:
            for need in sorted(inc.needs, key=lambda n: n.need_id):
                bridge = any(
                    o.kind == "approve_bls_bridge"
                    and o.unit_id == unit.unit_id
                    and o.bridges_need_id == need.need_id
                    for o in state.active_overrides
                )
                if unit.type not in ELIGIBLE_UNIT_TYPES[need.type] and not (
                    bridge and unit.type == "bls" and need.type == "als"
                ):
                    continue
                if lock and (old is None or (old.need_id or old.bridges_need_id) != need.need_id):
                    continue
                if any(
                    o.unit_id == unit.unit_id
                    and (
                        o.kind == "hold_unit"
                        or (o.kind == "forbid" and o.incident_id == inc.incident_id)
                    )
                    for o in state.active_overrides
                ):
                    continue
                if need.type == "water_rescue":
                    boat_route = getattr(routes, "boat_route", None)
                    if boat_route is None:
                        continue
                    route = boat_route(state, unit.position.coordinates, inc.location.coordinates)
                else:
                    route = _route(routes, state, unit.position, inc.location)
                degraded |= route.route_status == "provider_error"
                if route.route_status != "ok":
                    continue
                persons = None
                if need.type == "water_rescue":
                    facts = next(
                        (f for f in state.triage_facts if f.incident_id == inc.incident_id), None
                    )
                    count = (
                        next((f.count for f in facts.facts if f.key == "people_count"), None)
                        if facts
                        else None
                    )
                    if count is None or count.value is None or count.value > unit.capacity_persons:
                        continue
                    persons = count.value
                hospitals = [
                    f
                    for f in state.facilities
                    if isinstance(f, Hospital)
                    and f.ed_beds_available > 0
                    and "emergency" in f.capabilities
                ]
                transport = need.type in ("als", "bls") and not bridge
                for hospital in hospitals if transport else [None]:
                    onward = (
                        _route(routes, state, inc.location, hospital.location) if hospital else None
                    )
                    if onward and onward.route_status != "ok":
                        degraded |= onward.route_status == "provider_error"
                        continue
                    if (
                        lock
                        and old
                        and old.destination_facility_id
                        != (hospital.facility_id if hospital else None)
                    ):
                        continue
                    out.append(
                        Candidate(
                            unit,
                            inc,
                            need,
                            route,
                            hospital.facility_id if hospital else None,
                            onward,
                            lock=lock,
                            bridge=bridge,
                            persons=persons,
                        )
                    )
        if lock and not any(c.unit == unit and c.lock for c in out):
            raise DomainError(409, "NO_VALID_PLAN", "Locked task has no valid route or capacity")
    for inc in active:
        for need in inc.needs:
            if need.type != "shelter_places":
                continue
            for facility in sorted(state.facilities, key=lambda f: f.facility_id):
                if not isinstance(facility, Shelter):
                    continue
                capacity = min(need.quantity, facility.capacity_persons - facility.occupied_persons)
                route = _route(routes, state, inc.location, facility.location)
                if capacity > 0 and route.route_status == "ok":
                    out.append(
                        Candidate(None, inc, need, route, facility.facility_id, capacity=capacity)
                    )
    for zone in state.reserve_zones:
        for kind in zone.required_types:
            ids = []
            unknown = False
            for unit in state.units:
                if unit.status != "available" or not (
                    unit.type == kind or (kind == "bls" and unit.type == "als")
                ):
                    continue
                route = _route(routes, state, unit.position, zone.reference_point)
                unknown |= route.route_status == "provider_error"
                if (
                    route.route_status == "ok"
                    and route.duration_s is not None
                    and route.duration_s <= zone.coverage_eta_s
                ):
                    ids.append(unit.unit_id)
            coverage[f"{zone.zone_id}:{kind.value}"] = ids
            if unknown:
                coverage[f"?{zone.zone_id}:{kind.value}"] = []
    return out, coverage, degraded


def allocate(
    state: StateSnapshot, routes: Routes, *, budget_s: float | None = None, baseline: bool = False
) -> Plan:
    state = effective_state(state)
    started = monotonic()
    needs = [
        (i, n)
        for i in sorted(state.incidents, key=lambda x: x.incident_id)
        if i.status == "active"
        for n in sorted(i.needs, key=lambda x: x.need_id)
    ]
    limits = state.policy.limits
    if (
        len(state.units) > limits.units
        or len(needs) > limits.need_records
        or sum(n.quantity for _, n in needs) > limits.demand_quanta
        or sum(len(z.required_types) for z in state.reserve_zones) > limits.reserve_pairs
    ):
        raise DomainError(422, "POLICY_LIMIT_EXCEEDED", "World exceeds declared solver bounds")
    rows, cover, degraded = candidates(state, routes)
    costs = state.policy.costs
    weights = state.policy.severity_weights
    old = {a.unit_id: a for a in state.approved_plan.assignments} if state.approved_plan else {}
    model = cp_model.CpModel()
    xs = [model.new_int_var(0, c.capacity, f"x{i}") for i, c in enumerate(rows)]
    for unit in state.units:
        selected = [
            x for c, x in zip(rows, xs, strict=True) if c.unit and c.unit.unit_id == unit.unit_id
        ]
        model.add(sum(selected) <= 1)
        if any(c.unit and c.unit.unit_id == unit.unit_id and c.lock for c in rows):
            model.add(sum(selected) == 1)
    for override in state.active_overrides:
        if override.kind in ("pin", "approve_bls_bridge"):
            matches = [
                x
                for c, x in zip(rows, xs, strict=True)
                if c.unit
                and c.unit.unit_id == override.unit_id
                and c.need.need_id == (override.need_id or override.bridges_need_id)
            ]
            if not matches:
                raise DomainError(
                    409, "OVERRIDE_INFEASIBLE", "Override has no eligible reachable target"
                )
            model.add(sum(matches) == 1)
    for facility in state.facilities:
        cap = (
            facility.ed_beds_available
            if isinstance(facility, Hospital)
            else facility.capacity_persons - facility.occupied_persons
        )
        model.add(
            sum(x for c, x in zip(rows, xs, strict=True) if c.facility == facility.facility_id)
            <= cap
        )
    unmet: dict[str, Any] = {}
    for _inc, need in needs:
        missing_var = model.new_int_var(0, need.quantity, need.need_id)
        model.add(
            missing_var
            + sum(
                x
                for c, x in zip(rows, xs, strict=True)
                if c.need.need_id == need.need_id and not c.bridge
            )
            == need.quantity
        )
        unmet[need.need_id] = missing_var
    reserves: list[Any] = []
    for key, ids in cover.items():
        if key.startswith("?"):
            continue
        free = [
            1 - sum(x for c, x in zip(rows, xs, strict=True) if c.unit and c.unit.unit_id == uid)
            for uid in ids
        ]
        shortage = model.new_bool_var(f"reserve_{key}")
        model.add(sum(free) == 0).only_enforce_if(shortage)
        model.add(sum(free) >= 1).only_enforce_if(shortage.Not())
        reserves.append(shortage)

    def cost(c: Candidate) -> int:
        if not c.unit:
            return 0
        previous = old.get(c.unit.unit_id)
        moved = (
            previous is not None
            and (previous.need_id or previous.bridges_need_id) != c.need.need_id
        )
        return (
            weights[c.incident.severity] * min(c.route.duration_s or 0, costs.travel_cap_s)
            + costs.reassignment * moved
            + costs.als_on_bls * (c.unit.type == "als" and c.need.type == "bls")
        )

    objectives: list[Any] = [
        sum(unmet[n.need_id] for i, n in needs if i.severity == s) for s in Severity
    ]
    objectives += [
        sum(
            unmet[n.need_id]
            * weights[i.severity]
            * min(max(0, state.sim_time_s - i.created_sim_time_s), costs.waiting_cap_s)
            for i, n in needs
        ),
        sum(cost(c) * x for c, x in zip(rows, xs, strict=True))
        + costs.reserve_shortfall * sum(reserves),
    ]
    deadline = monotonic() + (
        budget_s if budget_s is not None else state.policy.solver_budget_ms / 1000
    )
    values: list[int] | None = None
    completed: list[str] = []
    tie_complete = False
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 7
    if not baseline:
        for tier, objective in zip(state.policy.objective_tiers, objectives, strict=True):
            left = deadline - monotonic()
            if left <= 0:
                break
            solver.parameters.max_time_in_seconds = left
            model.minimize(objective)
            status = solver.solve(model)
            if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                values = [solver.value(x) for x in xs]
            if status != cp_model.OPTIMAL:
                break
            completed.append(tier.value)
            model.add(objective == solver.value(objective))
        if len(completed) == 6:
            tie_complete = True
            # Fix every candidate in canonical order: bounded, no objective perturbation.
            for x in xs:
                if deadline <= monotonic():
                    tie_complete = False
                    break
                solver.parameters.max_time_in_seconds = deadline - monotonic()
                model.maximize(x)
                status = solver.solve(model)
                if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                    values = [solver.value(v) for v in xs]
                if status != cp_model.OPTIMAL:
                    tie_complete = False
                    break
                model.add(x == solver.value(x))
    fallback = values is None
    if fallback:
        values = greedy(state, rows)
        completed = []
    assert values is not None
    chosen = [(c, v) for c, v in zip(rows, values, strict=True) if v]
    version = max([p.version for p in (state.approved_plan, state.current_proposal) if p] + [0]) + 1
    plan_id = f"plan_{state.session_id}_{version}_{state.planning_sequence}"
    assignments: list[dict[str, Any]] = []
    allocations: list[dict[str, Any]] = []
    used: dict[str, int] = {}
    for c, value in chosen:
        if c.facility:
            used[c.facility] = used.get(c.facility, 0) + value
        if c.unit:
            previous = old.get(c.unit.unit_id)
            same = (
                previous
                and (previous.need_id or previous.bridges_need_id) == c.need.need_id
                and previous.destination_facility_id == c.facility
            )
            assignments.append(
                dict(
                    assignment_id=previous.assignment_id
                    if same and previous is not None
                    else f"asgn_{version}_{c.unit.unit_id}",
                    unit_id=c.unit.unit_id,
                    incident_id=c.incident.incident_id,
                    need_id=None if c.bridge else c.need.need_id,
                    role="bridge" if c.bridge else "primary",
                    satisfies_need=not c.bridge,
                    bridges_need_id=c.need.need_id if c.bridge else None,
                    eta_s=c.route.duration_s,
                    locked=c.lock,
                    persons=c.persons,
                    destination_facility_id=c.facility,
                    route=c.route,
                    onward_route=c.onward,
                    reasons=[
                        dict(
                            code="UNIT_LOCKED" if c.lock else "ELIGIBLE_ALLOCATION",
                            params={"eta_s": c.route.duration_s},
                        )
                    ],
                )
            )
        else:
            f = next(f for f in state.facilities if f.facility_id == c.facility)
            assert isinstance(f, Shelter)
            allocations.append(
                dict(
                    allocation_id=f"alloc_{version}_{c.need.need_id}_{c.facility}",
                    facility_id=c.facility,
                    incident_id=c.incident.incident_id,
                    need_id=c.need.need_id,
                    persons=value,
                    free_after_persons=f.capacity_persons
                    - f.occupied_persons
                    - used[c.facility or ""],
                    route=c.route,
                )
            )
    flags: list[dict[str, Any]] = []

    def flag(code: str, **extra: Any) -> None:
        flags.append(
            dict(
                flag_id=f"flag_{version}_{len(flags) + 1}",
                code=code,
                severity="critical"
                if code.startswith("ALS_UNMET") or code == "CRITICAL_NEED_UNMET"
                else "info"
                if code in ("PROVISIONAL_NEED", "SOLVER_TIME_LIMIT")
                else "warning",
                requires_ack=code not in ("PROVISIONAL_NEED", "SOLVER_TIME_LIMIT"),
                message=code.replace("_", " "),
                **extra,
            )
        )

    missing_rows: list[dict[str, Any]] = []
    counts = [0, 0, 0, 0]
    waiting = 0
    for inc, need in needs:
        fulfilled = sum(v for c, v in chosen if c.need.need_id == need.need_id and not c.bridge)
        missing = need.quantity - fulfilled
        if need.basis == "provisional_unknown":
            flag("PROVISIONAL_NEED", incident_id=inc.incident_id, need_id=need.need_id)
        if missing:
            age = max(0, state.sim_time_s - inc.created_sim_time_s)
            counts[list(Severity).index(inc.severity)] += missing
            waiting += missing * weights[inc.severity] * min(age, costs.waiting_cap_s)
            missing_rows.append(
                dict(
                    need_id=need.need_id,
                    incident_id=inc.incident_id,
                    type=need.type,
                    quantity_unmet=missing,
                    severity=inc.severity,
                    basis=need.basis,
                    waiting_s=age,
                    reasons=[
                        dict(
                            code="NO_ALS_AVAILABLE"
                            if need.type == "als"
                            else "NO_ELIGIBLE_CAPACITY",
                            params={},
                        )
                    ],
                )
            )
            if need.type == "als":
                bridge_options = []
                for u in sorted(state.units, key=lambda u: u.unit_id):
                    if u.type != "bls" or u.status not in ("available", "returning", "en_route"):
                        continue
                    previous = old.get(u.unit_id)
                    previous_incident = next(
                        (
                            i
                            for i in state.incidents
                            if previous and i.incident_id == previous.incident_id
                        ),
                        None,
                    )
                    remaining = (
                        _route(routes, state, u.position, previous_incident.location)
                        if previous_incident
                        else None
                    )
                    if lock_for(state, u, remaining):
                        continue
                    option_route = _route(routes, state, u.position, inc.location)
                    if option_route.route_status != "ok":
                        continue
                    occupying = next((a for a in assignments if a["unit_id"] == u.unit_id), None)
                    consequences = []
                    if occupying and occupying["need_id"]:
                        consequences.append(
                            dict(metric="unmet_need", need_id=occupying["need_id"], delta=1)
                        )
                    bridge_options.append(
                        dict(
                            unit_id=u.unit_id,
                            eta_s=option_route.duration_s,
                            cost_of_taking=consequences,
                        )
                    )
                missing_rows[-1]["bridge_candidates"] = sorted(
                    bridge_options, key=lambda b: (b["eta_s"], b["unit_id"])
                )[:3]
            code = (
                "ALS_UNMET"
                if need.type == "als"
                else "CRITICAL_NEED_UNMET"
                if inc.severity == "critical"
                else "NEED_UNMET"
            )
            if need.type == "als" and any(
                c.bridge and c.need.need_id == need.need_id for c, _ in chosen
            ):
                code = "ALS_UNMET_BLS_BRIDGING"
            flag(code, incident_id=inc.incident_id, need_id=need.need_id)
    assigned = {a["unit_id"] for a in assignments}
    coverage = []
    for key, ids in cover.items():
        if key.startswith("?"):
            continue
        zone, kind = key.split(":")
        available = sorted(set(ids) - assigned)
        status_name = (
            "covered" if available else "coverage_unknown" if f"?{key}" in cover else "uncovered"
        )
        coverage.append(
            dict(zone_id=zone, resource_type=kind, status=status_name, available_unit_ids=available)
        )
        if not available:
            flag(
                "RESERVE_COVERAGE_UNKNOWN"
                if status_name == "coverage_unknown"
                else "RESERVE_UNCOVERED",
                zone_id=zone,
                resource_type=kind,
                since_sim_time_s=state.sim_time_s,
            )
    if fallback:
        flag("FALLBACK_HEURISTIC")
    elif len(completed) < 6:
        flag("SOLVER_TIME_LIMIT")
    if degraded:
        flag("ROUTING_DEGRADED")
    operating = sum(cost(c) * v for c, v in chosen) + costs.reserve_shortfall * sum(
        c["status"] != "covered" for c in coverage
    )
    added, changed, released = [], [], []
    for a in assignments:
        prev = old.get(a["unit_id"])
        row = dict(
            unit_id=a["unit_id"],
            **{
                "from": dict(
                    state="assigned",
                    incident_id=prev.incident_id,
                    need_id=prev.need_id,
                    eta_s=prev.eta_s,
                )
                if prev
                else dict(state="available")
            },
            to=dict(
                state="assigned",
                incident_id=a["incident_id"],
                need_id=a["need_id"],
                eta_s=a["eta_s"],
            ),
        )
        if prev is None:
            added.append(row)
        elif prev.assignment_id != a["assignment_id"]:
            changed.append(row)
    for uid, prev in old.items():
        if uid not in assigned:
            released.append(
                dict(
                    unit_id=uid,
                    **{"from": dict(state="assigned", incident_id=prev.incident_id)},
                    to=dict(state="available"),
                )
            )
    data = dict(
        schema_version="1.0",
        session_id=state.session_id,
        plan_id=plan_id,
        version=version,
        state="proposed",
        based_on_planning_sequence=state.planning_sequence,
        created_sim_time_s=state.sim_time_s,
        created_at=datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        policy_version=state.policy.policy_version,
        supersedes_approved_plan_id=state.approved_plan.plan_id if state.approved_plan else None,
        solver=dict(
            engine="greedy_fallback" if fallback else "ortools_cp_sat",
            status="FALLBACK" if fallback else "OPTIMAL" if len(completed) == 6 else "FEASIBLE",
            wall_time_ms=int((monotonic() - started) * 1000),
            seed=7,
            workers=1,
            objective_vector=[*counts, waiting, operating],
            completed_tiers=completed,
            lexicographic_complete=len(completed) == 6,
            tie_break_complete=tie_complete,
        ),
        assignments=assignments,
        facility_allocations=allocations,
        unmet_needs=missing_rows,
        flags=flags,
        coverage=coverage,
        diff=dict(
            against_plan_id=state.approved_plan.plan_id if state.approved_plan else None,
            changed=changed,
            added=added,
            released=released,
            unchanged_count=len(assignments) - len(added) - len(changed),
            newly_unmet=[
                n["need_id"]
                for n in missing_rows
                if not state.approved_plan
                or n["need_id"] not in {u.need_id for u in state.approved_plan.unmet_needs}
            ],
            totals=dict(
                weighted_eta_delta_s=sum(
                    weights[c.incident.severity] * (c.route.duration_s or 0)
                    for c, v in chosen
                    if c.unit
                )
                - sum(
                    weights[
                        next(i for i in state.incidents if i.incident_id == a.incident_id).severity
                    ]
                    * a.eta_s
                    for a in old.values()
                ),
                units_moved=len(changed),
                units_added=len(added),
                units_released=len(released),
                needs_unmet=sum(counts),
                zones_uncovered=sum(c["status"] != "covered" for c in coverage),
            ),
        ),
        soft_consequences=[],
    )
    plan = Plan.model_validate(data)
    validate_plan(state, plan)
    return plan


def unit_id(c: Candidate) -> str:
    return c.unit.unit_id if c.unit else ""


def greedy(state: StateSnapshot, rows: list[Candidate]) -> list[int]:
    """Nearest feasible fallback/baseline; honours identical pins, capacities and locks."""
    selected = [0] * len(rows)
    used: set[str] = set()
    served: dict[str, int] = {}
    facilities: dict[str, int] = {}
    forced = {
        (o.unit_id, o.need_id or o.bridges_need_id)
        for o in state.active_overrides
        if o.kind in ("pin", "approve_bls_bridge")
    }
    order = sorted(
        range(len(rows)),
        key=lambda j: (
            not (
                rows[j].lock
                or (rows[j].unit and (unit_id(rows[j]), rows[j].need.need_id) in forced)
            ),
            list(Severity).index(rows[j].incident.severity),
            rows[j].incident.created_sim_time_s,
            rows[j].route.duration_s,
            unit_id(rows[j]) if rows[j].unit else "",
            rows[j].facility or "",
        ),
    )
    for j in order:
        c = rows[j]
        if c.unit and c.unit.unit_id in used:
            continue
        remaining = c.need.quantity - served.get(c.need.need_id, 0)
        quantity = 1 if c.bridge else min(c.capacity, remaining)
        if c.facility:
            f = next(f for f in state.facilities if f.facility_id == c.facility)
            cap = (
                f.ed_beds_available
                if isinstance(f, Hospital)
                else f.capacity_persons - f.occupied_persons
            )
            quantity = min(quantity, cap - facilities.get(c.facility, 0))
        if quantity <= 0:
            continue
        selected[j] = quantity
        if c.unit:
            used.add(c.unit.unit_id)
        if not c.bridge:
            served[c.need.need_id] = served.get(c.need.need_id, 0) + quantity
        if c.facility:
            facilities[c.facility] = facilities.get(c.facility, 0) + quantity
    for c in rows:
        if (
            c.unit
            and (c.lock or (c.unit.unit_id, c.need.need_id) in forced)
            and not any(
                v and r.unit == c.unit and r.need == c.need
                for r, v in zip(rows, selected, strict=True)
            )
        ):
            raise DomainError(409, "NO_VALID_PLAN", "Fallback cannot honour locked tasks or pins")
    return selected


def validate_plan(state: StateSnapshot, plan: Plan) -> None:
    from app.contracts.validation import plan_world_errors

    state = effective_state(state)

    validate_capacity_and_locks(state, plan)
    errors = plan_world_errors(plan, state.units, state.incidents, state.policy)
    units = {u.unit_id: u for u in state.units}
    for a in plan.assignments:
        unit = units.get(a.unit_id)
        if unit and unit.status in UNAVAILABLE:
            errors.add("UNIT_UNAVAILABLE")
        if a.route.flood_version != max(
            [r.route.flood_version for r in plan.assignments] + [a.route.flood_version]
        ):
            errors.add("ROUTE_VERSION_MISMATCH")
    if errors:
        raise DomainError(409, "NO_VALID_PLAN", ", ".join(sorted(errors)))


def validate_capacity_and_locks(state: StateSnapshot, plan: Plan) -> None:
    """Independent gate: recompute membership, quantities and reservations from output."""
    errors: set[str] = set()
    units = {u.unit_id: u for u in state.units}
    needs = {n.need_id: (i, n) for i in state.incidents if i.status == "active" for n in i.needs}
    facilities = {f.facility_id: f for f in state.facilities}
    served: dict[str, int] = {}
    used: dict[str, int] = {}
    assigned = {a.unit_id: a for a in plan.assignments}
    for a in plan.assignments:
        pair = needs.get(a.need_id or a.bridges_need_id or "")
        if pair is None or pair[0].incident_id != a.incident_id:
            errors.add("UNKNOWN_NEED")
            continue
        inc, need = pair
        u = units.get(a.unit_id)
        if u is None:
            continue
        if u.status not in ("available", "returning", "en_route", "on_scene", "transporting"):
            errors.add("UNIT_UNAVAILABLE")
        if a.role == "bridge":
            if (
                u.type != "bls"
                or need.type != "als"
                or not any(
                    o.kind == "approve_bls_bridge"
                    and o.unit_id == a.unit_id
                    and o.bridges_need_id == need.need_id
                    for o in state.active_overrides
                )
            ):
                errors.add("BRIDGE_NOT_AUTHORIZED")
        else:
            served[need.need_id] = served.get(need.need_id, 0) + 1
        if a.route.from_ != u.position or a.route.to != inc.location:
            errors.add("ROUTE_ENDPOINT_MISMATCH")
        if need.type in ("als", "bls") and a.role == "primary":
            facility = facilities.get(a.destination_facility_id or "")
            if not isinstance(facility, Hospital) or a.onward_route is None:
                errors.add("HOSPITAL_REQUIRED")
            elif a.onward_route.from_ != inc.location or a.onward_route.to != facility.location:
                errors.add("ROUTE_ENDPOINT_MISMATCH")
        if a.destination_facility_id:
            used[a.destination_facility_id] = used.get(a.destination_facility_id, 0) + 1
        if need.type == "water_rescue" and (a.persons is None or a.persons > u.capacity_persons):
            errors.add("BOAT_CAPACITY")
    for allocation in plan.facility_allocations:
        facility = facilities.get(allocation.facility_id)
        pair = needs.get(allocation.need_id)
        if (
            not isinstance(facility, Shelter)
            or pair is None
            or pair[1].type != "shelter_places"
            or pair[0].incident_id != allocation.incident_id
        ):
            errors.add("FACILITY_INELIGIBLE")
            continue
        if (
            not allocation.route
            or allocation.route.route_status != "ok"
            or allocation.route.to != facility.location
            or allocation.route.from_ != pair[0].location
        ):
            errors.add("ROUTE_UNAVAILABLE")
        used[allocation.facility_id] = used.get(allocation.facility_id, 0) + allocation.persons
        served[allocation.need_id] = served.get(allocation.need_id, 0) + allocation.persons
    for fid, amount in used.items():
        facility = facilities.get(fid)
        cap = (
            facility.ed_beds_available
            if isinstance(facility, Hospital)
            else facility.capacity_persons - facility.occupied_persons
            if isinstance(facility, Shelter)
            else -1
        )
        if amount > cap:
            errors.add("CAPACITY_EXCEEDED")
    missing = {n.need_id: n.quantity_unmet for n in plan.unmet_needs}
    if len(missing) != len(plan.unmet_needs):
        errors.add("DUPLICATE_UNMET")
    for nid, (_, need) in needs.items():
        if served.get(nid, 0) + missing.get(nid, 0) != need.quantity:
            errors.add("DEMAND_ACCOUNTING")
    if set(missing) - set(needs):
        errors.add("UNKNOWN_NEED")
    for old in state.approved_plan.assignments if state.approved_plan else []:
        unit = units.get(old.unit_id)
        if not unit or unit.status in UNAVAILABLE or unit.current_task is None:
            continue
        target = assigned.get(unit.unit_id)
        is_locked = unit.status in ("on_scene", "transporting") or (
            unit.status == "en_route" and old.eta_s <= state.policy.near_arrival_lock_s
        )
        if is_locked and (target is None or target.assignment_id != old.assignment_id):
            errors.add("LOCK_VIOLATION")
    for o in state.active_overrides:
        target = assigned.get(o.unit_id or "")
        if o.kind == "pin" and (target is None or target.need_id != o.need_id):
            errors.add("PIN_VIOLATION")
        if o.kind == "hold_unit" and target:
            errors.add("HOLD_VIOLATION")
        if o.kind == "forbid" and target and target.incident_id == o.incident_id:
            errors.add("FORBID_VIOLATION")
        if o.kind == "approve_bls_bridge" and (
            target is None or target.bridges_need_id != o.bridges_need_id
        ):
            errors.add("BRIDGE_NOT_AUTHORIZED")
    if errors:
        raise DomainError(409, "NO_VALID_PLAN", ", ".join(sorted(errors)))


def effective_state(state: StateSnapshot) -> StateSnapshot:
    ids = {o.need_id for o in state.active_overrides if o.kind == "downgrade_need"}
    if not ids:
        return state
    result = state.model_copy(deep=True)
    for incident in result.incidents:
        for need in incident.needs:
            if need.need_id in ids and need.basis != "provisional_unknown":
                raise DomainError(
                    409, "CONFIRMED_NEED_CANNOT_DOWNGRADE", "Confirmed danger invalidates downgrade"
                )
        incident.needs = [n for n in incident.needs if n.need_id not in ids]
    return result
