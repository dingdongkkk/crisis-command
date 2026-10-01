"""Live command boundary for allocation, intake events, overrides and demo controls."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Callable
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
    AnswerCommand,
    ApprovalAccepted,
    ApproveCommand,
    DemoAdvanceCommand,
    DuplicateResolveCommand,
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
    IncidentCategoryChangedPayload,
    IncidentPayload,
    ModelAdapterDegradedPayload,
    OverrideEndedPayload,
    OverridePayload,
    OverrideRejectedPayload,
    PlanProposedPayload,
    ReportLinkedToIncidentPayload,
    ReportReceivedPayload,
    TriageFactConfirmedPayload,
    TriageFactsExtractedPayload,
)
from app.contracts.plan import Plan
from app.contracts.state import StateSnapshot
from app.domain.assessment import assess
from app.domain.commands import DomainError, NewEvent
from app.intake.model_adapter import FactModel
from app.intake.service import IntakeService
from app.intake.session import IntakeSession
from app.planning.allocator import allocate
from app.planning.override_checks import override_conflicts
from app.planning.service import Planner, event
from app.storage.event_store import Decision, problem

router = APIRouter()

# Facts only an operator records (not asked by intake, not used for allocation). 0008: the
# Medical ID gate reads ``caller_is_patient``; missing or unknown denies access.
OPERATOR_ONLY_FACTS = frozenset({"caller_is_patient"})


def planner(request: Request) -> Planner:
    result: Planner = request.app.state.planner
    return result


def intake_service(request: Request) -> IntakeService:
    result: IntakeService = request.app.state.intake
    return result


def _save_intake(session_id: str, intake: IntakeSession) -> Callable[[sqlite3.Connection], None]:
    data = json.dumps(intake.to_state(), sort_keys=True)

    def write(conn: sqlite3.Connection) -> None:
        conn.execute(
            "INSERT OR REPLACE INTO intake_sessions VALUES (?, ?)",
            (f"{session_id}:{intake.incident_id}", data),
        )

    return write


def report_decision(
    state: StateSnapshot, command: ReportCommand, model: FactModel | None = None
) -> Decision:
    if command.sim_time_s < state.sim_time_s:
        raise DomainError(409, "INVALID_TRANSITION", "Simulation time went backwards")
    number = state.as_of_sequence + 1
    report_id, incident_id = f"report_{number}", f"incident_{number}"
    intake = IntakeSession(incident_id, model=model)
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
    if intake.model_status == "unavailable":
        events.append(
            NewEvent(
                "ModelAdapterDegraded",
                "incident",
                incident_id,
                ModelAdapterDegradedPayload(
                    adapter="model_adapter", cause=intake.model_failure or "TRANSPORT_ERROR"
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
    save_intake = _save_intake(state.session_id, intake)

    def save_text(conn: sqlite3.Connection) -> None:
        conn.execute(
            "INSERT INTO report_text VALUES (?, ?)",
            (f"{state.session_id}:{report_id}", command.text),
        )
        save_intake(conn)

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
    key = _require_key(idempotency_key)
    # The optional model runs here, before the writer lock; its outcome is replayed inside.
    model = intake_service(request).prefetch(command.text)
    result = _store(request).execute(
        method="POST",
        path="/reports",
        key=key,
        body=command.model_dump(mode="json", by_alias=True),
        expected_session_id=command.expected_session_id,
        decide=lambda state: report_decision(state, command, model),
        actor=OPERATOR,
    )
    return _result_response(result)


@router.post(
    "/reports/{report_id}/answers", response_model=ReportAccepted, responses=PROBLEM_RESPONSES
)
def answer(
    request: Request, report_id: str, command: AnswerCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    store = _store(request)

    def decide(state: StateSnapshot) -> Decision:
        report = next((r for r in state.reports if r.report_id == report_id), None)
        incident_id = report.linked_incident_id if report else None
        incident = next(
            (i for i in state.incidents if i.incident_id == incident_id and i.status == "active"),
            None,
        )
        saved = store.intake_state(state.session_id, incident_id) if incident_id else None
        if report is None or incident is None or saved is None:
            raise DomainError(404, "NOT_FOUND", "Unknown report or no active intake")
        intake = IntakeSession.from_state(saved)
        current = next(
            (f for f in state.triage_facts if f.incident_id == incident.incident_id), None
        )
        confirmed = [f for f in current.facts if f.confirmed_by_operator] if current else []
        # Operator confirmations outrank intake answers and must survive this re-extraction.
        for f in confirmed:
            if f.key in intake.facts and f.value is not None:
                intake.facts[f.key].value = f.value
                intake.facts[f.key].source = "operator"
                intake.facts[f.key].confirmed_by_operator = True
        pending = intake.pending_question()
        if pending is None or pending.fact_key != command.fact_key:
            raise DomainError(
                409,
                "NO_PENDING_QUESTION",
                "That question is not awaiting an answer",
                current={"pending_fact_key": pending.fact_key if pending else None},
            )
        was_escalated = bool(intake.escalation_reasons(state.sim_time_s))
        if command.fact_key == "people_count":
            intake.answer_count(None, state.sim_time_s)  # counts are confirmed by the operator
        else:
            intake.answer(command.fact_key, command.answer, state.sim_time_s)
        intake.next_question(state.sim_time_s)
        facts = intake.triage_facts(state.sim_time_s)
        by_key = {f.key: f for f in confirmed}
        facts.facts = [by_key.get(f.key, f) for f in facts.facts] + [
            f for f in confirmed if f.key not in {x.key for x in facts.facts}
        ]
        assessed = assess(incident, facts, state.policy)
        events = [
            event(
                state,
                "TriageFactsExtracted",
                TriageFactsExtractedPayload(triage_facts=facts),
                "incident",
                incident.incident_id,
            ),
            event(
                state,
                "IncidentAssessed",
                IncidentPayload(incident=assessed),
                "incident",
                incident.incident_id,
            ),
        ]
        if facts.escalation.escalated and not was_escalated:
            events.append(
                event(
                    state,
                    "EscalatedToHuman",
                    EscalatedToHumanPayload(
                        incident_id=incident.incident_id, reasons=facts.escalation.reasons
                    ),
                    "incident",
                    incident.incident_id,
                )
            )
        return Decision(
            events,
            lambda es: (
                200,
                dict(
                    report_id=report_id,
                    incident_id=incident.incident_id,
                    sequence=es[-1].sequence,
                    escalated=facts.escalation.escalated,
                ),
            ),
            _save_intake(state.session_id, intake),
        )

    result = store.execute(
        method="POST",
        path=f"/reports/{report_id}/answers",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=decide,
        actor=OPERATOR,
    )
    if result.status == 200:
        planner(request).recompute()
    return _result_response(result)


SEVERITY_ORDER = ("low", "medium", "high", "critical")


def merge_duplicate_demand(original: Incident, candidate: Incident) -> Incident:
    """Linking must never drop demand only the second caller reported (CC-12 P1).

    Per need type keep the larger quantity and the stronger basis; keep the higher severity.
    The candidate's needs then leave planning when it becomes ``merged_duplicate``.
    """
    needs = {n.type: n for n in original.needs}
    for n in candidate.needs:
        mine = needs.get(n.type)
        if mine is None:
            needs[n.type] = n.model_copy(
                update={"need_id": f"{original.incident_id}_{n.type.value}"}
            )
            continue
        stronger = "confirmed" in (mine.basis, n.basis)
        needs[n.type] = mine.model_copy(
            update={
                "quantity": max(mine.quantity, n.quantity),
                "basis": "confirmed" if stronger else mine.basis,
                "reasons": mine.reasons if mine.quantity >= n.quantity else n.reasons,
            }
        )
    severity = max(
        (original.severity, candidate.severity), key=lambda s: SEVERITY_ORDER.index(s.value)
    )
    return original.model_copy(
        update={"needs": sorted(needs.values(), key=lambda n: n.need_id), "severity": severity}
    )


@router.post("/incidents/{incident_id}/duplicates/{report_id}/resolve", responses=PROBLEM_RESPONSES)
def resolve_duplicate(
    request: Request,
    incident_id: str,
    report_id: str,
    command: DuplicateResolveCommand,
    idempotency_key: IdempotencyKey = None,
) -> JSONResponse:
    """Operator decision on a duplicate candidate; never automatic (0007 AS-07, 0008).

    ``incident_id`` is the original incident; ``report_id`` is the report whose incident was
    flagged as a possible duplicate of it.
    """

    def decide(state: StateSnapshot) -> Decision:
        active = {i.incident_id: i for i in state.incidents if i.status == "active"}
        report = next((r for r in state.reports if r.report_id == report_id), None)
        candidate = active.get(report.linked_incident_id or "") if report else None
        if incident_id not in active or report is None or candidate is None:
            raise DomainError(404, "NOT_FOUND", "Unknown active incident or report")
        if incident_id not in candidate.duplicate_candidate_of:
            raise DomainError(
                409,
                "NOT_A_DUPLICATE_CANDIDATE",
                "This report's incident is not a duplicate candidate of that incident",
                current={"duplicate_candidate_of": list(candidate.duplicate_candidate_of)},
            )
        payload = ReportLinkedToIncidentPayload(
            report_id=report_id, incident_id=incident_id, resolution=command.resolution
        )
        events = []
        if command.resolution == "linked":
            merged = merge_duplicate_demand(active[incident_id], candidate)
            if merged != active[incident_id]:
                events.append(
                    event(
                        state,
                        "IncidentAssessed",
                        IncidentPayload(incident=merged),
                        "incident",
                        incident_id,
                    )
                )
        events.append(event(state, "ReportLinkedToIncident", payload, "report", report_id))
        return Decision(
            events,
            lambda es: (
                200,
                dict(
                    incident_id=incident_id,
                    report_id=report_id,
                    candidate_incident_id=candidate.incident_id,
                    resolution=command.resolution,
                    sequence=es[-1].sequence,
                ),
            ),
        )

    result = _store(request).execute(
        method="POST",
        path=f"/incidents/{incident_id}/duplicates/{report_id}/resolve",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=decide,
        actor=OPERATOR,
    )
    if result.status == 200:
        planner(request).recompute()
    return _result_response(result)


@router.get("/plans/{plan_id}", response_model=Plan, responses=PROBLEM_RESPONSES)
def get_plan(request: Request, plan_id: str) -> Plan:
    state = _store(request).state()
    for p in (state.current_proposal, state.approved_plan):
        if p and p.plan_id == plan_id:
            return p
    raise DomainError(404, "NOT_FOUND", "Unknown current plan")


@router.post(
    "/plans/recompute",
    status_code=202,
    response_model=RecomputeAccepted,
    responses=PROBLEM_RESPONSES,
)
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
            [], lambda _: (202, dict(status="computing", planning_sequence=state.planning_sequence))
        ),
        actor=OPERATOR,
    )
    if result.status == 202:
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
        known = {f.key for f in facts.facts} if facts else set()
        if (
            incident is None
            or facts is None
            or (fact_key not in known and fact_key not in OPERATOR_ONLY_FACTS)
        ):
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
        if fact_key in known:
            facts.facts = [fact if f.key == fact_key else f for f in facts.facts]
        else:
            facts.facts = [*facts.facts, fact]
        assessed = assess(incident, facts, state.policy)
        events = [
            event(
                state,
                "TriageFactConfirmed",
                TriageFactConfirmedPayload(incident_id=incident_id, fact=fact),
                "incident",
                incident_id,
            )
        ]
        if assessed.category != incident.category:
            # A confirmed danger turned a routine call into an emergency (CC-12 P1): record
            # why, and hand it to a human, never silently.
            events.append(
                event(
                    state,
                    "IncidentCategoryChanged",
                    IncidentCategoryChangedPayload(
                        incident=assessed,
                        from_category=incident.category,
                        reason="CONFIRMED_DANGER",
                        triggering_fact_keys=[fact_key],
                    ),
                    "incident",
                    incident_id,
                )
            )
            events.append(
                event(
                    state,
                    "EscalatedToHuman",
                    EscalatedToHumanPayload(
                        incident_id=incident_id,
                        reasons=[
                            "LIFE_THREAT_INDICATED"
                            if fact_key
                            in (
                                "conscious",
                                "breathing_normally",
                                "chest_pain",
                                "severe_bleeding",
                                "trapped",
                            )
                            else "CONFIRMED_DANGER"
                        ],
                    ),
                    "incident",
                    incident_id,
                )
            )
        else:
            events.append(
                event(
                    state,
                    "IncidentAssessed",
                    IncidentPayload(incident=assessed),
                    "incident",
                    incident_id,
                )
            )
        return Decision(events, lambda es: (200, {"sequence": es[-1].sequence}))

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
    conflicts: list[dict[str, Any]] = []
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
            conflicts = override_conflicts(trial, command, planner(request).routes)
            if conflicts:
                raise DomainError(
                    409, "OVERRIDE_CONFLICT", "Override conflicts with a hard constraint"
                )
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
            coded = (
                conflicts
                if error.code == "OVERRIDE_CONFLICT" and conflicts
                else [dict(code=error.code, detail=error.title)]
            )
            payload = OverrideRejectedPayload.model_validate(
                dict(
                    override_id=oid,
                    kind=command.kind,
                    unit_id=command.unit_id,
                    need_id=command.need_id,
                    incident_id=command.incident_id,
                    bridges_need_id=command.bridges_need_id,
                    conflicts=coded,
                )
            )
            body = problem(error)
            if error.code == "OVERRIDE_CONFLICT":
                # 0004: the operator sees each broken constraint, as recorded in the event.
                body.update(override_id=oid, conflicts=payload.model_dump(mode="json")["conflicts"])
            return Decision(
                [event(state, "OverrideRejected", payload)],
                lambda _: (error.status, body),
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


@router.post("/demo/advance", responses=PROBLEM_RESPONSES)
def advance_demo(
    request: Request, command: DemoAdvanceCommand, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    from app.domain.demo import advance

    result = _store(request).execute(
        method="POST",
        path="/demo/advance",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=lambda state: advance(state, command),
        actor=OPERATOR,
    )
    if result.status == 200:
        planner(request).recompute()
    return _result_response(result)
