"""Live command boundary for allocation, intake events, overrides and demo controls."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.routes import (
    OPERATOR,
    PROBLEM_RESPONSES,
    IdempotencyKey,
    _require_key,
    _result_response,
    _store,
)
from app.contracts.commands import (
    ApprovalAccepted,
    ApproveCommand,
    FactConfirmCommand,
    OverrideCommand,
    OverrideRecorded,
    RecomputeAccepted,
    RecomputeCommand,
    ReportAccepted,
    ReportCommand,
)
from app.contracts.entities import Incident, Override, Report, TriageFact
from app.contracts.events import (
    DuplicateCandidateFlaggedPayload,
    EscalatedToHumanPayload,
    IncidentPayload,
    OverrideEndedPayload,
    OverridePayload,
    OverrideRejectedPayload,
    PlanProposedPayload,
    ReportReceivedPayload,
    TriageFactConfirmedPayload,
    TriageFactsExtractedPayload,
)
from app.contracts.plan import Plan
from app.contracts.state import StateSnapshot
from app.domain.assessment import assess
from app.domain.commands import DomainError, NewEvent
from app.intake.session import IntakeSession
from app.planning.allocator import allocate
from app.planning.service import Planner, event
from app.storage.event_store import Decision, problem

router = APIRouter()


def planner(request: Request) -> Planner:
    result: Planner = request.app.state.planner
    return result


def report_decision(state: StateSnapshot, command: ReportCommand) -> Decision:
    if command.sim_time_s < state.sim_time_s:
        raise DomainError(409, "INVALID_TRANSITION", "Simulation time went backwards")
    number = state.as_of_sequence + 1
    report_id, incident_id = f"report_{number}", f"incident_{number}"
    intake = IntakeSession(incident_id)
    intake.add_report(report_id, command.text, command.sim_time_s)
    intake.next_question(command.sim_time_s)
    facts = intake.triage_facts(command.sim_time_s)
    inc = Incident.model_validate(
        dict(
            incident_id=incident_id,
            category=intake.category,
            kind=intake.kind,
            severity="low",
            assumed_facts=[],
            location=command.location,
            created_sim_time_s=command.sim_time_s,
            status="active",
            report_ids=[report_id],
            needs=[],
            duplicate_candidate_of=[],
        )
    )
    inc = assess(inc, facts, state.policy)
    from app.domain.duplicates import duplicate_candidates

    inc.duplicate_candidate_of = duplicate_candidates(state, inc)
    report = Report.model_validate(
        dict(
            report_id=report_id,
            received_sim_time_s=command.sim_time_s,
            received_at=datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            channel=command.channel,
            text_ref=dict(
                store="report_text",
                report_id=report_id,
                text_sha256=hashlib.sha256(command.text.encode()).hexdigest(),
                length_chars=len(command.text),
            ),
            location=command.location,
            location_source=command.location_source,
            linked_incident_id=incident_id,
        )
    )
    events = [
        NewEvent(
            "ReportReceived",
            "report",
            report_id,
            ReportReceivedPayload(report=report),
            command.sim_time_s,
        ),
        NewEvent(
            "TriageFactsExtracted",
            "incident",
            incident_id,
            TriageFactsExtractedPayload(triage_facts=facts),
            command.sim_time_s,
        ),
        NewEvent(
            "IncidentCreated",
            "incident",
            incident_id,
            IncidentPayload(incident=inc),
            command.sim_time_s,
        ),
    ]
    for candidate in inc.duplicate_candidate_of:
        events.append(
            NewEvent(
                "DuplicateCandidateFlagged",
                "incident",
                incident_id,
                DuplicateCandidateFlaggedPayload(
                    report_id=report_id,
                    candidate_incident_id=candidate,
                    reasons=["SPATIAL_TIME_MATCH"],
                ),
                command.sim_time_s,
            )
        )
    if facts.escalation.escalated:
        events.append(
            NewEvent(
                "EscalatedToHuman",
                "incident",
                incident_id,
                EscalatedToHumanPayload(incident_id=incident_id, reasons=facts.escalation.reasons),
                command.sim_time_s,
            )
        )

    def save_text(conn: sqlite3.Connection) -> None:
        conn.execute(
            "INSERT INTO report_text VALUES (?, ?)",
            (f"{state.session_id}:{report_id}", command.text),
        )

    return Decision(
        events,
        lambda es: (
            201,
            dict(
                report_id=report_id,
                incident_id=incident_id,
                sequence=es[-1].sequence,
                escalated=facts.escalation.escalated,
            ),
        ),
        save_text,
    )


@router.post(
    "/reports", status_code=201, response_model=ReportAccepted, responses=PROBLEM_RESPONSES
)
def reports(
    request: Request, command: ReportCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    result = _store(request).execute(
        method="POST",
        path="/reports",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json", by_alias=True),
        expected_session_id=command.expected_session_id,
        decide=lambda state: report_decision(state, command),
        actor=OPERATOR,
    )
    return _result_response(result)


@router.get("/plans/{plan_id}", response_model=Plan, responses=PROBLEM_RESPONSES)
def get_plan(request: Request, plan_id: str) -> Plan:
    state = _store(request).state()
    for p in (state.current_proposal, state.approved_plan):
        if p and p.plan_id == plan_id:
            return p
    raise DomainError(404, "NOT_FOUND", "Unknown current plan")


@router.post("/plans/recompute", response_model=RecomputeAccepted, responses=PROBLEM_RESPONSES)
def recompute(
    request: Request, command: RecomputeCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    result = _store(request).execute(
        method="POST",
        path="/plans/recompute",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=lambda state: Decision(
            [], lambda _: (200, dict(status="computing", planning_sequence=state.planning_sequence))
        ),
        actor=OPERATOR,
    )
    if result.status == 200:
        planner(request).recompute()
    return _result_response(result)


@router.post(
    "/plans/{plan_id}/approve", response_model=ApprovalAccepted, responses=PROBLEM_RESPONSES
)
def approve(
    request: Request, plan_id: str, command: ApproveCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    result = _store(request).execute(
        method="POST",
        path=f"/plans/{plan_id}/approve",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=lambda state: planner(request).approval(state, plan_id, command),
        actor=OPERATOR,
    )
    return _result_response(result)


@router.post("/incidents/{incident_id}/facts/{fact_key}/confirm", responses=PROBLEM_RESPONSES)
def confirm(
    request: Request,
    incident_id: str,
    fact_key: str,
    command: FactConfirmCommand,
    idempotency_key: IdempotencyKey = None,
) -> JSONResponse:
    def decide(state: StateSnapshot) -> Decision:
        incident = next(
            (i for i in state.incidents if i.incident_id == incident_id and i.status == "active"),
            None,
        )
        facts = next(
            (f.model_copy(deep=True) for f in state.triage_facts if f.incident_id == incident_id),
            None,
        )
        if incident is None or facts is None or fact_key not in {f.key for f in facts.facts}:
            raise DomainError(404, "NOT_FOUND", "Unknown active incident or fact")
        data: dict[str, Any] = dict(
            key=fact_key,
            source="operator",
            evidence=[],
            updated_sim_time_s=state.sim_time_s,
            confirmed_by_operator=True,
        )
        if fact_key == "people_count":
            data["count"] = dict(
                value=command.count, status="unknown" if command.count is None else "known"
            )
        elif command.value is not None:
            data["value"] = command.value
        else:
            raise DomainError(422, "VALIDATION_FAILED", "Tri-state value required")
        fact = TriageFact.model_validate(data)
        facts.facts = [fact if f.key == fact_key else f for f in facts.facts]
        assessed = assess(incident, facts, state.policy)
        return Decision(
            [
                event(
                    state,
                    "TriageFactConfirmed",
                    TriageFactConfirmedPayload(incident_id=incident_id, fact=fact),
                    "incident",
                    incident_id,
                ),
                event(
                    state,
                    "IncidentAssessed",
                    IncidentPayload(incident=assessed),
                    "incident",
                    incident_id,
                ),
            ],
            lambda es: (200, {"sequence": es[-1].sequence}),
        )

    return _result_response(
        _store(request).execute(
            method="POST",
            path=f"/incidents/{incident_id}/facts/{fact_key}/confirm",
            key=_require_key(idempotency_key),
            body=command.model_dump(mode="json"),
            expected_session_id=command.expected_session_id,
            decide=decide,
            actor=OPERATOR,
        )
    )


@router.post("/overrides", response_model=OverrideRecorded, responses=PROBLEM_RESPONSES)
def override(
    request: Request, command: OverrideCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    # Preflight solve outside SQLite; compare the planning sequence again inside the transaction.
    initial = _store(request).state()
    target = initial.current_proposal or initial.approved_plan
    oid = f"override_{uuid.uuid4().hex[:12]}"
    rejection: DomainError | None = None
    proposed: Plan | None = None
    record: Override | None = None
    try:
        if (
            target is None
            or target.plan_id != command.expected_plan_id
            or initial.planning_sequence != command.expected_planning_sequence
        ):
            raise DomainError(409, "STALE_PLAN", "Override is bound to an old plan")
        trial = initial.model_copy(deep=True)
        if command.replaces_override_id:
            trial.active_overrides = [
                o for o in trial.active_overrides if o.override_id != command.replaces_override_id
            ]
        if command.kind == "revoke":
            if command.revokes_override_id not in {o.override_id for o in trial.active_overrides}:
                raise DomainError(404, "NOT_FOUND", "Unknown active override")
            trial.active_overrides = [
                o for o in trial.active_overrides if o.override_id != command.revokes_override_id
            ]
        else:
            if command.kind == "downgrade_need":
                need = next(
                    (n for i in trial.incidents for n in i.needs if n.need_id == command.need_id),
                    None,
                )
                if need is None or need.basis != "provisional_unknown":
                    raise DomainError(
                        409,
                        "CONFIRMED_NEED_CANNOT_DOWNGRADE",
                        "Only provisional needs may be downgraded",
                    )
            if command.unit_id is not None and command.unit_id not in {
                u.unit_id for u in trial.units
            }:
                raise DomainError(409, "UNKNOWN_UNIT", "Unknown unit")
            if command.kind == "forbid" and command.incident_id not in {
                i.incident_id for i in trial.incidents
            }:
                raise DomainError(409, "UNKNOWN_INCIDENT", "Unknown incident")
            data = command.model_dump(exclude={"expected_plan_id", "expected_planning_sequence"})
            record = Override.model_validate(
                {**data, "override_id": oid, "status": "active", "created_by": OPERATOR}
            )
            trial.active_overrides.append(record)
        proposed = allocate(trial, planner(request).routes)
    except DomainError as exc:
        rejection = exc

    def decide(state: StateSnapshot) -> Decision:
        error = rejection
        if state.planning_sequence != command.expected_planning_sequence:
            error = DomainError(409, "STALE_PLAN", "World changed during override validation")
        if error:
            payload = OverrideRejectedPayload.model_validate(
                dict(
                    override_id=oid,
                    kind=command.kind,
                    unit_id=command.unit_id,
                    conflicts=[dict(code=error.code, detail=error.title)],
                )
            )
            return Decision(
                [event(state, "OverrideRejected", payload)],
                lambda _: (error.status, problem(error)),
            )
        events = []
        for old in (command.replaces_override_id, command.revokes_override_id):
            if old:
                events.append(
                    event(
                        state,
                        "OverrideRevoked",
                        OverrideEndedPayload(override_id=old, reason="OPERATOR_REVOKED"),
                    )
                )
        if record:
            events.append(event(state, "OverrideAccepted", OverridePayload(override=record)))
        assert proposed is not None
        proposed.based_on_planning_sequence = state.as_of_sequence + len(events)
        events.append(event(state, "PlanProposed", PlanProposedPayload(plan=proposed)))
        return Decision(
            events,
            lambda es: (
                200,
                dict(
                    override_id=oid,
                    status="active",
                    sequence=es[-1].sequence,
                    recompute="computing",
                ),
            ),
        )

    return _result_response(
        _store(request).execute(
            method="POST",
            path="/overrides",
            key=_require_key(idempotency_key),
            body=command.model_dump(mode="json"),
            expected_session_id=command.expected_session_id,
            decide=decide,
            actor=OPERATOR,
        )
    )
