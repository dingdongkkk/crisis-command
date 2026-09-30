from __future__ import annotations

import pytest

from app.contracts.entities import CurrentTask, Incident, Route
from app.contracts.enums import UnitStatus
from app.contracts.state import StateSnapshot
from app.domain.assessment import assess
from app.domain.commands import DomainError
from app.intake.session import IntakeSession
from app.planning.allocator import allocate
from app.storage.event_store import EventStore


class FixedRoutes:
    def __init__(self, seconds: int = 300, unavailable: bool = False) -> None:
        self.seconds, self.unavailable = seconds, unavailable

    def route(
        self, state: StateSnapshot, origin: tuple[float, float], destination: tuple[float, float]
    ) -> Route:
        return Route.model_validate(
            {
                "route_id": "route_test",
                "from": {"type": "Point", "coordinates": origin},
                "to": {"type": "Point", "coordinates": destination},
                "route_status": "unavailable" if self.unavailable else "ok",
                "provider": "fixture",
                "flood_version": 0,
                "duration_s": None if self.unavailable else self.seconds,
                "distance_m": None if self.unavailable else 1000,
                "geometry": None
                if self.unavailable
                else {"type": "LineString", "coordinates": [origin, destination]},
                "unavailable_reason": "NO_ROUTE" if self.unavailable else None,
            }
        )


def incident(
    name: str = "incident_test", text: str = "Chest pain", at: int = 0
) -> tuple[Incident, IntakeSession]:
    session = IntakeSession(name)
    session.add_report(f"report_{name}", text, at)
    i = Incident.model_validate(
        dict(
            incident_id=name,
            category=session.category,
            kind=session.kind,
            severity="low",
            assumed_facts=[],
            location={"type": "Point", "coordinates": [77.60, 12.97]},
            created_sim_time_s=at,
            status="active",
            report_ids=session.report_ids,
            needs=[],
            duplicate_candidate_of=[],
        )
    )
    return i, session


def world(store: EventStore, text: str = "Chest pain") -> StateSnapshot:
    state = store.state()
    i, session = incident(text=text)
    facts = session.triage_facts(0)
    state.incidents = [assess(i, facts, state.policy)]
    state.triage_facts = [facts]
    return state


def test_polarity_and_safe_confirmation(store: EventStore) -> None:
    state = store.state()
    i, session = incident(text="Accident with injuries")
    unknown = assess(i, session.triage_facts(0), state.policy)
    assert any(n.type == "als" for n in unknown.needs)
    session.answer("conscious", "no", 1, operator=True)
    dangerous = assess(i, session.triage_facts(1), state.policy)
    assert next(n for n in dangerous.needs if n.type == "als").basis == "confirmed"
    for key, value in state.policy.dangerous_values.items():
        session.answer(key, "yes" if value == "no" else "no", 2, operator=True)
    safe = assess(i, session.triage_facts(2), state.policy)
    assert not any(n.type == "als" for n in safe.needs)
    assert any(n.type == "bls" for n in safe.needs)


def test_zero_fleet_and_no_route_keep_unmet(store: EventStore) -> None:
    state = world(store)
    for no_fleet in (True, False):
        state.units = [] if no_fleet else store.state().units
        plan = allocate(state, FixedRoutes(unavailable=True))
        assert plan.assignments == []
        assert any(n.type == "als" for n in plan.unmet_needs)
        assert any(f.code == "ALS_UNMET" and f.requires_ack for f in plan.flags)


def test_allocate_capacity_ties_timeout(store: EventStore) -> None:
    state = world(store)
    a, b = allocate(state, FixedRoutes()), allocate(state, FixedRoutes())
    assert a.solver.lexicographic_complete and a.solver.tie_break_complete
    assert [(x.unit_id, x.need_id) for x in a.assignments] == [
        (x.unit_id, x.need_id) for x in b.assignments
    ]
    assert len({x.unit_id for x in a.assignments}) == len(a.assignments)
    fallback = allocate(state, FixedRoutes(), budget_s=0)
    assert fallback.solver.engine == "greedy_fallback"
    assert any(f.code == "FALLBACK_HEURISTIC" for f in fallback.flags)
    for f in state.facilities:
        if f.kind == "hospital":
            f.ed_beds_available = 0
    assert allocate(state, FixedRoutes()).assignments == []


def test_locked_and_broken_down(store: EventStore) -> None:
    state = world(store)
    initial = allocate(state, FixedRoutes())
    state.approved_plan = initial
    assignment = initial.assignments[0]
    unit = next(u for u in state.units if u.unit_id == assignment.unit_id)
    unit.status = UnitStatus.ON_SCENE
    unit.current_task = CurrentTask(
        assignment_id=assignment.assignment_id,
        incident_id=assignment.incident_id,
        need_id=assignment.need_id,
    )
    assert allocate(state, FixedRoutes()).assignments[0].unit_id == unit.unit_id
    with pytest.raises(DomainError, match="Locked task"):
        allocate(state, FixedRoutes(unavailable=True))
    unit.status = UnitStatus.BROKEN_DOWN
    unit.current_task = None
    assert unit.unit_id not in {a.unit_id for a in allocate(state, FixedRoutes()).assignments}


def test_reserve_never_overrides_service(store: EventStore) -> None:
    state = world(store)
    state.units = [next(u for u in state.units if u.type == "als")]
    need = state.incidents[0].needs[0]
    from app.contracts.enums import NeedType, Severity

    need.type = NeedType.BLS
    state.incidents[0].severity = Severity.LOW
    base = state.reserve_zones[0]
    from app.contracts.enums import UnitType

    state.reserve_zones = [
        base.model_copy(
            update={
                "zone_id": f"zone_{j}",
                "required_types": [UnitType.ALS, UnitType.BLS],
                "coverage_eta_s": 3600,
            }
        )
        for j in range(6)
    ]
    result = allocate(state, FixedRoutes(seconds=3600))
    assert result.unmet_needs == []
    assert result.solver.objective_vector == [0, 0, 0, 0, 0, 15300]
