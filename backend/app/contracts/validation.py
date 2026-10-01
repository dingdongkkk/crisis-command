"""Contract validation helpers shared by tests, fixtures and (later) the API.

``schema`` errors come from the Pydantic models. ``domain`` checks need world context
(unit types, need types, policy) and are pure functions; CC-05/CC-08 reuse them in the
policy gate. ``fixture`` checks apply only to seeded demo data.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import ValidationError

from . import ADAPTERS
from .common import Point, in_demo_bounds
from .entities import Incident, Unit
from .enums import ELIGIBLE_UNIT_TYPES, AssignmentRole, LockReason
from .plan import Plan
from .state import Policy

GENERIC_CODE = "VALIDATION_FAILED"


def error_codes(exc: ValidationError) -> set[str]:
    """Named contract codes in a ValidationError; unnamed Pydantic errors map to generic."""
    codes = set()
    for err in exc.errors():
        kind = str(err["type"])
        codes.add(kind if kind.isupper() else GENERIC_CODE)
    return codes


def schema_errors(name: str, value: Any) -> set[str]:
    try:
        ADAPTERS[name].validate_python(value)
    except ValidationError as exc:
        return error_codes(exc)
    return set()


def plan_world_errors(
    plan: Plan,
    units: Iterable[Unit],
    incidents: Iterable[Incident],
    policy: Policy,
) -> set[str]:
    """Hard-constraint checks (0003 H1, H3, H4, H7) that need world context."""
    errors: set[str] = set()
    units_by_id: Mapping[str, Unit] = {u.unit_id: u for u in units}
    needs = {n.need_id: n for i in incidents for n in i.needs}
    seen: set[str] = set()
    for assignment in plan.assignments:
        if assignment.unit_id in seen:
            errors.add("DUPLICATE_UNIT")
        seen.add(assignment.unit_id)
        unit = units_by_id.get(assignment.unit_id)
        if unit is None:
            errors.add("UNKNOWN_UNIT")
            continue
        need_id = (
            assignment.need_id
            if assignment.role is AssignmentRole.PRIMARY
            else assignment.bridges_need_id
        )
        need = needs.get(need_id or "")
        if need is None:
            errors.add("UNKNOWN_NEED")
            continue
        if (
            assignment.role is AssignmentRole.PRIMARY
            and unit.type not in ELIGIBLE_UNIT_TYPES[need.type]
        ):
            errors.add("TYPE_INELIGIBLE")
        if (
            assignment.locked is LockReason.NEAR_ARRIVAL
            and assignment.eta_s > policy.near_arrival_lock_s
        ):
            errors.add("LOCK_THRESHOLD_EXCEEDED")
        if assignment.route.duration_s != assignment.eta_s:
            errors.add("ETA_ROUTE_MISMATCH")
    return errors


def fixture_errors(point: Point) -> set[str]:
    return set() if in_demo_bounds(point) else {"OUTSIDE_DEMO_BOUNDS"}
