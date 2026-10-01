"""Structural override preflight (0004): coded conflicts before any solve.

Each conflict names the hard constraint an operator override would break, so the console can
say *why* it was refused. ``OVERRIDE_INFEASIBLE`` stays reserved for solver-level
infeasibility that no single structural rule explains.
"""

from __future__ import annotations

from typing import Any

from app.contracts.commands import OverrideCommand
from app.contracts.enums import ELIGIBLE_UNIT_TYPES
from app.contracts.state import StateSnapshot
from app.domain.commands import UNAVAILABLE
from app.planning.allocator import Routes, lock_for

PIN_KINDS = ("pin", "approve_bls_bridge")


def _conflict(
    code: str, unit_id: str | None, detail: str, override_id: str | None = None
) -> dict[str, Any]:
    out: dict[str, Any] = {"code": code, "unit_id": unit_id, "detail": detail}
    if override_id:
        out["override_id"] = override_id
    return out


def override_conflicts(
    state: StateSnapshot, command: OverrideCommand, routes: Routes
) -> list[dict[str, Any]]:
    unit = next((u for u in state.units if u.unit_id == command.unit_id), None)
    if unit is None or command.kind in ("revoke", "downgrade_need"):
        return []
    uid = unit.unit_id
    incidents = {i.incident_id: i for i in state.incidents if i.status == "active"}
    needs = {n.need_id: (i, n) for i in incidents.values() for n in i.needs}
    target_need = command.need_id or command.bridges_need_id
    target = needs.get(target_need or "")
    target_incident = target[0].incident_id if target else command.incident_id
    replaced = command.replaces_override_id
    active = [o for o in state.active_overrides if o.override_id != replaced]
    conflicts: list[dict[str, Any]] = []

    # A unit on scene, transporting or about to arrive keeps its task (0003/0004).
    old = next(
        (
            a
            for a in (state.approved_plan.assignments if state.approved_plan else [])
            if unit.current_task and a.assignment_id == unit.current_task.assignment_id
        ),
        None,
    )
    current = incidents.get(old.incident_id) if old else None
    route_now = (
        routes.route(state, unit.position.coordinates, current.location.coordinates)
        if current
        else None
    )
    lock = lock_for(state, unit, route_now)
    locked_need = (old.need_id or old.bridges_need_id) if old else None
    if lock and old:
        breaks_lock = {
            "pin": locked_need != target_need,
            "approve_bls_bridge": locked_need != target_need,
            "hold_unit": True,
            "forbid": old.incident_id == command.incident_id,
        }.get(command.kind.value, False)
        if breaks_lock:
            conflicts.append(_conflict("UNIT_LOCKED", uid, f"{uid} is {lock} at {old.incident_id}"))

    if command.kind in PIN_KINDS:
        if unit.status in UNAVAILABLE or unit.status == "at_facility":
            conflicts.append(_conflict("UNIT_NOT_AVAILABLE", uid, f"{uid} is {unit.status.value}"))
        if target is not None:
            incident, need = target
            if command.kind == "pin" and unit.type not in ELIGIBLE_UNIT_TYPES[need.type]:
                hint = (
                    "; use approve_bls_bridge" if unit.type == "bls" and need.type == "als" else ""
                )
                conflicts.append(
                    _conflict(
                        "TYPE_INELIGIBLE",
                        uid,
                        f"{unit.type.value} unit cannot satisfy a {need.type.value} need{hint}",
                    )
                )
            if command.kind == "approve_bls_bridge" and (unit.type != "bls" or need.type != "als"):
                conflicts.append(
                    _conflict(
                        "TYPE_INELIGIBLE",
                        uid,
                        "a bridge is a BLS unit covering an ALS need until ALS arrives",
                    )
                )
            if need.type == "water_rescue":
                conflicts.append(
                    _conflict(
                        "ROUTE_UNAVAILABLE",
                        uid,
                        "water access is not modelled; no route can be verified",
                    )
                )
            elif not conflicts or all(c["code"] == "UNIT_LOCKED" for c in conflicts):
                route = routes.route(
                    state, unit.position.coordinates, incident.location.coordinates
                )
                if route.route_status != "ok":
                    conflicts.append(
                        _conflict(
                            "ROUTE_UNAVAILABLE",
                            uid,
                            f"no usable road route from {uid} to {incident.incident_id}"
                            f" ({route.route_status})",
                        )
                    )
            pinned_elsewhere = [
                o
                for o in active
                if o.kind in PIN_KINDS
                and o.need_id == target_need
                and o.unit_id != uid
                and command.kind == "pin"
            ]
            if command.kind == "pin" and len(pinned_elsewhere) >= need.quantity:
                conflicts.append(
                    _conflict(
                        "CAPACITY_EXCEEDED",
                        uid,
                        f"{need.need_id} needs {need.quantity} and already has "
                        f"{len(pinned_elsewhere)} pinned",
                        pinned_elsewhere[0].override_id,
                    )
                )

    for o in active:
        if o.unit_id != uid:
            continue
        if command.kind in PIN_KINDS and o.kind in (*PIN_KINDS, "hold_unit"):
            conflicts.append(
                _conflict(
                    "DUPLICATE_UNIT_PIN",
                    uid,
                    f"{uid} already has an active {o.kind.value}",
                    o.override_id,
                )
            )
        elif command.kind in PIN_KINDS and o.kind == "forbid" and o.incident_id == target_incident:
            conflicts.append(
                _conflict(
                    "CONTRADICTS_OVERRIDE",
                    uid,
                    f"{uid} is forbidden from {target_incident}",
                    o.override_id,
                )
            )
        elif command.kind == "hold_unit" and o.kind in PIN_KINDS:
            conflicts.append(
                _conflict(
                    "CONTRADICTS_OVERRIDE",
                    uid,
                    f"{uid} is pinned by {o.override_id}",
                    o.override_id,
                )
            )
        elif command.kind == "forbid" and o.kind in PIN_KINDS:
            pinned = needs.get(o.need_id or o.bridges_need_id or "")
            if pinned and pinned[0].incident_id == command.incident_id:
                conflicts.append(
                    _conflict(
                        "CONTRADICTS_OVERRIDE",
                        uid,
                        f"{uid} is pinned to {command.incident_id} by {o.override_id}",
                        o.override_id,
                    )
                )
    return conflicts
