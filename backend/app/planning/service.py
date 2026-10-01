"""Planning outside the writer lock; publish, approve and deliver against fresh state."""

from __future__ import annotations

import threading
import uuid
from typing import Any

from app.contracts.commands import ApproveCommand
from app.contracts.entities import CurrentTask
from app.contracts.enums import DispatchState, UnitStatus
from app.contracts.events import (
    ApprovalRejectedPayload,
    DesiredAssignment,
    EnvelopeBase,
    HospitalPreAlertSimulatedPayload,
    OverrideEndedPayload,
    PlanApprovedPayload,
    PlanFailedPayload,
    PlanProposedPayload,
    PlanRevalidatedPayload,
    SimulatedDispatchEndedPayload,
    SimulatedDispatchQueuedPayload,
    SimulatedDispatchSentPayload,
)
from app.contracts.plan import Plan
from app.contracts.state import DispatchCommand, StateSnapshot
from app.domain.commands import UNAVAILABLE, DomainError, NewEvent
from app.planning.allocator import Routes, allocate, validate_plan
from app.routing.router import closures_key
from app.routing.service import active_closures
from app.storage.event_store import Decision, EventStore, problem

SYSTEM = {"kind": "system", "id": "planner"}


def event(
    state: StateSnapshot, kind: str, payload: Any, aggregate: str = "plan", ident: str = "planner"
) -> NewEvent:
    return NewEvent(kind, aggregate, ident, payload, state.sim_time_s)


def semantic(plan: Plan) -> dict[str, Any]:
    """Ignore identity and display timing, retain all operationally significant fields."""
    data = plan.model_dump(mode="json", by_alias=True)
    result = {
        key: data[key]
        for key in (
            "policy_version",
            "assignments",
            "facility_allocations",
            "unmet_needs",
            "flags",
            "coverage",
        )
    }
    for key in ("assignments", "facility_allocations", "flags"):
        for item in result[key]:
            for field in ("assignment_id", "allocation_id", "flag_id", "since_sim_time_s"):
                item.pop(field, None)
    for item in result["unmet_needs"]:
        item.pop("waiting_s", None)
    result["solver"] = {
        key: data["solver"][key] for key in ("engine", "status", "lexicographic_complete")
    }
    return result


class Planner:
    def __init__(self, store: EventStore, routes: Routes) -> None:
        self.store, self.routes = store, routes
        self._lock = threading.Lock()
        self._dirty = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._unsubscribe: Any = None

    def start(self) -> None:
        self._unsubscribe = self.store.subscribe(self.on_events)
        self._thread = threading.Thread(target=self._run, daemon=True, name="crisis-planner")
        self._thread.start()
        # Recover pending outbox without replaying already sent actions.
        self._dirty.set()

    def close(self) -> None:
        self._stop.set()
        self._dirty.set()
        if self._thread:
            self._thread.join(timeout=10)
        if self._unsubscribe:
            self._unsubscribe()

    def on_events(self, events: list[EnvelopeBase]) -> None:
        if any(e.affects_planning for e in events):
            self._dirty.set()

    def _run(self) -> None:
        while not self._stop.is_set():
            self._dirty.wait(1)
            if self._stop.is_set():
                break
            if not self._dirty.is_set():
                continue
            self._stop.wait(0.25)
            self._dirty.clear()
            try:
                self.deliver()
                self.recompute()
            except Exception:
                # Keep the process alive; record a visible failure and allow next change/retry.
                self.record_failure("PLANNING_FAILED")

    def record_failure(self, reason: str) -> None:
        state = self.store.state()

        def decide(current: StateSnapshot) -> Decision:
            payload = PlanFailedPayload(
                plan_id="failed",
                based_on_planning_sequence=current.planning_sequence,
                reasons=[reason],
            )
            return Decision(
                [event(current, "PlanFailed", payload)], lambda _: (200, {"status": "failed"})
            )

        self.store.execute(
            method="POST",
            path="/internal/plan-failure",
            key=str(uuid.uuid4()),
            body={},
            expected_session_id=state.session_id,
            decide=decide,
            actor=SYSTEM,
        )

    def recompute(self) -> None:
        with self._lock:
            state = self.store.state()
            if not state.incidents and not state.approved_plan:
                return
            invalid = []
            needs = {n.need_id: n for i in state.incidents if i.status == "active" for n in i.needs}
            for o in state.active_overrides:
                unit = next((u for u in state.units if u.unit_id == o.unit_id), None)
                need = needs.get(o.need_id or o.bridges_need_id or "")
                if (o.unit_id and (unit is None or unit.status in UNAVAILABLE)) or (
                    (o.need_id or o.bridges_need_id)
                    and (
                        need is None
                        or (o.kind == "downgrade_need" and need.basis != "provisional_unknown")
                    )
                ):
                    invalid.append(o.override_id)
            if invalid:

                def invalidate(current: StateSnapshot) -> Decision:
                    if current.planning_sequence != state.planning_sequence:
                        return Decision([], lambda _: (409, {}))
                    return Decision(
                        [
                            event(
                                current,
                                "OverrideInvalidated",
                                OverrideEndedPayload(override_id=oid, reason="WORLD_CHANGED"),
                            )
                            for oid in invalid
                        ],
                        lambda _: (200, {}),
                    )

                self.store.execute(
                    method="POST",
                    path="/internal/invalidate",
                    key=str(uuid.uuid4()),
                    body={},
                    expected_session_id=state.session_id,
                    decide=invalidate,
                    actor=SYSTEM,
                )
                state = self.store.state()
            try:
                plan = allocate(state, self.routes)
            except DomainError as exc:
                self.record_failure(exc.code)
                return

            def publish(current: StateSnapshot) -> Decision:
                if current.planning_sequence != state.planning_sequence:
                    self._dirty.set()
                    return Decision([], lambda _: (409, {"code": "STALE_PLAN"}))
                reference = current.current_proposal or current.approved_plan
                if reference and semantic(reference) == semantic(plan):
                    payload = PlanRevalidatedPayload(
                        plan_id=reference.plan_id,
                        checked_planning_sequence=current.planning_sequence,
                        checked_sim_time_s=current.sim_time_s,
                    )
                    # A stale *proposal* must be replaced with a newly bound proposal.
                    if (
                        current.current_proposal
                        and reference.based_on_planning_sequence != current.planning_sequence
                    ):
                        return Decision(
                            [event(current, "PlanProposed", PlanProposedPayload(plan=plan))],
                            lambda _: (200, {}),
                        )
                    return Decision(
                        [event(current, "PlanRevalidated", payload)], lambda _: (200, {})
                    )
                return Decision(
                    [event(current, "PlanProposed", PlanProposedPayload(plan=plan))],
                    lambda _: (200, {}),
                )

            self.store.execute(
                method="POST",
                path="/internal/recompute",
                key=str(uuid.uuid4()),
                body={},
                expected_session_id=state.session_id,
                decide=publish,
                actor=SYSTEM,
            )

    def approval(self, state: StateSnapshot, plan_id: str, command: ApproveCommand) -> Decision:
        plan = state.current_proposal
        code = None
        if plan is None:
            code = (
                "PLAN_NOT_PROPOSED"
                if state.approved_plan and state.approved_plan.plan_id == plan_id
                else "STALE_PLAN"
            )
        elif (
            plan.plan_id != plan_id
            or plan.version != command.expected_plan_version
            or plan.based_on_planning_sequence != command.expected_planning_sequence
            or state.planning_sequence != command.expected_planning_sequence
        ):
            code = "STALE_PLAN"
        elif {f.flag_id for f in plan.flags if f.requires_ack} - set(command.acknowledged_flag_ids):
            code = "UNACKNOWLEDGED_FLAGS"
        if code:
            error = DomainError(
                409,
                code,
                "Approval rejected",
                current={"planning_sequence": state.planning_sequence},
            )
            return Decision(
                [
                    event(
                        state,
                        "ApprovalRejected",
                        ApprovalRejectedPayload(plan_id=plan_id, code=code),
                    )
                ],
                lambda _: (409, problem(error)),
            )
        assert plan is not None
        validate_plan(state, plan, self.routes)
        units = {u.unit_id: u for u in state.units}
        commands: list[DispatchCommand] = []
        desired = []
        target_units = {a.unit_id for a in plan.assignments}
        for a in plan.assignments:
            unit = units[a.unit_id]
            if unit.current_task and unit.current_task.assignment_id == a.assignment_id:
                continue
            revision = (unit.desired_revision or 0) + 1
            desired.append(
                DesiredAssignment(
                    unit_id=unit.unit_id, assignment_id=a.assignment_id, desired_revision=revision
                )
            )
            commands.append(
                DispatchCommand.model_validate(
                    dict(
                        session_id=state.session_id,
                        outbox_key=f"{state.session_id}:{plan_id}:assign:{a.assignment_id}",
                        plan_id=plan_id,
                        action="assign",
                        unit_id=unit.unit_id,
                        assignment_id=a.assignment_id,
                        incident_id=a.incident_id,
                        desired_revision=revision,
                        state="pending",
                        simulated=True,
                    )
                )
            )
        for unit in state.units:
            if unit.current_task and unit.unit_id not in target_units:
                revision = (unit.desired_revision or 0) + 1
                aid = unit.current_task.assignment_id
                desired.append(
                    DesiredAssignment(
                        unit_id=unit.unit_id, assignment_id=aid, desired_revision=revision
                    )
                )
                commands.append(
                    DispatchCommand.model_validate(
                        dict(
                            session_id=state.session_id,
                            outbox_key=f"{state.session_id}:{plan_id}:release:{aid}",
                            plan_id=plan_id,
                            action="release",
                            unit_id=unit.unit_id,
                            assignment_id=aid,
                            desired_revision=revision,
                            state="pending",
                            simulated=True,
                        )
                    )
                )
        for c in list(commands):
            assignment = next(
                (a for a in plan.assignments if a.assignment_id == c.assignment_id), None
            )
            if c.action == "assign" and assignment and assignment.destination_facility_id:
                commands.append(
                    DispatchCommand.model_validate(
                        {
                            **c.model_dump(),
                            "action": "hospital_pre_alert",
                            "outbox_key": (
                                f"{state.session_id}:{plan_id}:hospital_pre_alert:{c.assignment_id}"
                            ),
                        }
                    )
                )
        pending = [
            event(
                state,
                "SimulatedDispatchCancelled",
                SimulatedDispatchEndedPayload(outbox_key=c.outbox_key, reason="SUPERSEDED"),
            )
            for c in state.outbox
            if c.state == "pending"
        ]
        keys = [c.outbox_key for c in commands]
        payload = PlanApprovedPayload(
            plan_id=plan_id,
            version=plan.version,
            based_on_planning_sequence=command.expected_planning_sequence,
            acknowledged_flag_ids=command.acknowledged_flag_ids,
            outbox_keys=keys,
            desired_assignments=desired,
            note_present=bool(command.note),
        )
        events = [
            *pending,
            event(state, "PlanApproved", payload),
            *(
                event(
                    state,
                    "SimulatedDispatchQueued",
                    SimulatedDispatchQueuedPayload(command=c),
                    "outbox",
                    c.outbox_key,
                )
                for c in commands
            ),
        ]
        return Decision(
            events,
            lambda appended: (
                200,
                dict(
                    plan_id=plan_id,
                    state="approved",
                    sequence=next(e.sequence for e in appended if e.event_type == "PlanApproved"),
                    outbox_keys=keys,
                ),
            ),
        )

    def _still_routable(self, state: StateSnapshot, command: DispatchCommand) -> bool:
        """Is the assignment still drivable under the flood closures now in effect?

        Computed before the writer lock (routing is not done under it); the decision then
        checks the closures did not change in between (CC-12 P1: a flood after approval must
        not let a queued simulated dispatch go out on a closed road)."""
        if command.action != "assign":
            return True
        unit = next((u for u in state.units if u.unit_id == command.unit_id), None)
        incident = next((i for i in state.incidents if i.incident_id == command.incident_id), None)
        if unit is None or incident is None:
            return True  # the fence below rejects these cases with its own reason
        plan = state.approved_plan
        assignment = (
            next((a for a in plan.assignments if a.assignment_id == command.assignment_id), None)
            if plan
            else None
        )
        need = next(
            (n for n in incident.needs if assignment and n.need_id == assignment.need_id), None
        )
        if need is not None and need.type == "water_rescue":
            return True  # boat routes are not road routes; unchanged behaviour
        route = self.routes.route(state, unit.position.coordinates, incident.location.coordinates)
        return route.route_status == "ok"

    def deliver(self) -> None:
        state = self.store.state()
        closures = closures_key(active_closures(state))
        for command in state.outbox:
            if command.state != DispatchState.PENDING:
                continue
            routable = self._still_routable(state, command)

            def decide(
                current: StateSnapshot,
                command: DispatchCommand = command,
                routable: bool = routable,
            ) -> Decision:
                c = next((c for c in current.outbox if c.outbox_key == command.outbox_key), None)
                if c is None or c.state != DispatchState.PENDING:
                    return Decision([], lambda _: (200, {}))
                if closures_key(active_closures(current)) != closures or not routable:
                    # Road network changed (or route closed) since approval: never send; the
                    # replan proposes a new route for human approval.
                    payload = SimulatedDispatchEndedPayload(
                        outbox_key=c.outbox_key, reason="ROUTE_INVALIDATED"
                    )
                    return Decision(
                        [event(current, "SimulatedDispatchCancelled", payload)], lambda _: (200, {})
                    )
                unit = next((u for u in current.units if u.unit_id == c.unit_id), None)
                plan = current.approved_plan
                valid = (
                    unit is not None
                    and plan is not None
                    and plan.plan_id == c.plan_id
                    and unit.desired_revision == c.desired_revision
                    and unit.status not in UNAVAILABLE
                )
                if c.action == "release":
                    valid = valid and bool(
                        unit
                        and unit.current_task
                        and unit.current_task.assignment_id == c.assignment_id
                    )
                assignment = (
                    next((a for a in plan.assignments if a.assignment_id == c.assignment_id), None)
                    if plan
                    else None
                )
                if c.action == "assign":
                    valid = valid and assignment is not None
                if not valid:
                    payload = SimulatedDispatchEndedPayload(
                        outbox_key=c.outbox_key, reason="STALE_DELIVERY_FENCE"
                    )
                    return Decision(
                        [event(current, "SimulatedDispatchCancelled", payload)], lambda _: (200, {})
                    )
                if c.action == "hospital_pre_alert":
                    if assignment is None or assignment.destination_facility_id is None:
                        return Decision(
                            [
                                event(
                                    current,
                                    "SimulatedDispatchCancelled",
                                    SimulatedDispatchEndedPayload(
                                        outbox_key=c.outbox_key, reason="STALE_DELIVERY_FENCE"
                                    ),
                                )
                            ],
                            lambda _: (200, {}),
                        )
                    alert = HospitalPreAlertSimulatedPayload(
                        outbox_key=c.outbox_key,
                        hospital_id=assignment.destination_facility_id,
                        incident_id=assignment.incident_id,
                        capability_needed="EMERGENCY",
                        simulated=True,
                    )
                    sent = SimulatedDispatchSentPayload(
                        outbox_key=c.outbox_key,
                        action=c.action,
                        assignment_id=c.assignment_id,
                        simulated=True,
                    )
                    return Decision(
                        [
                            event(current, "HospitalPreAlertSimulated", alert),
                            event(current, "SimulatedDispatchSent", sent),
                        ],
                        lambda _: (200, {}),
                    )
                assert unit is not None
                updated = unit.model_copy(deep=True)
                updated.status = (
                    UnitStatus.AVAILABLE if c.action == "release" else UnitStatus.EN_ROUTE
                )
                updated.current_task = (
                    None
                    if c.action == "release"
                    else CurrentTask(
                        assignment_id=c.assignment_id,
                        incident_id=c.incident_id or "unknown",
                        need_id=assignment.need_id if assignment else None,
                    )
                )
                payload_sent = SimulatedDispatchSentPayload(
                    outbox_key=c.outbox_key,
                    action=c.action,
                    unit_id=c.unit_id,
                    assignment_id=c.assignment_id,
                    unit_after=updated,
                    simulated=True,
                )
                # No external side effect: the committed event is the simulated delivery.
                return Decision(
                    [event(current, "SimulatedDispatchSent", payload_sent)], lambda _: (200, {})
                )

            self.store.execute(
                method="POST",
                path="/internal/deliver",
                key=str(uuid.uuid4()),
                body={"outbox_key": command.outbox_key},
                expected_session_id=state.session_id,
                decide=decide,
                actor=SYSTEM,
            )
