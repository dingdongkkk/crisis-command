"""Seeded synthetic progression. Operator approval remains a separate command."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Callable
from typing import Any

from app.contracts import EVENT_ADAPTER
from app.contracts.commands import DemoAdvanceCommand, ReportCommand, UnitStatusCommand
from app.contracts.events import EVENT_CATALOG, PlanningTickCommittedPayload
from app.contracts.state import StateSnapshot
from app.domain.commands import DomainError, NewEvent, unit_status
from app.domain.projection import apply
from app.storage.event_store import Decision

STEPS = {"T+0": 0, "T+2": 120, "T+5": 300, "T+10": 600}
REPORTS: dict[int, list[tuple[str, tuple[float, float]]]] = {
    0: [
        (
            "Chest pain, not breathing normally. I am the patient; I want a human.",
            (77.5946, 12.9716),
        ),
        ("Is Outer Ring Road open near Bellandur?", (77.6000, 12.9750)),
        ("Flat tyre on ORR, the car is fine and nobody is hurt", (77.6200, 12.9700)),
    ],
    120: [
        ("Road accident with injuries, two people, severe bleeding.", (77.6100, 12.9850)),
        ("Gas leak and gas smell. Evacuate 20 people. No one injured.", (77.5800, 12.9900)),
    ],
    300: [
        ("Our car is stranded in flood; water rising, 3 people trapped.", (77.6200, 12.9700)),
        ("Water rising around a stranded car, 3 people trapped.", (77.6201, 12.9701)),
    ],
    600: [
        (
            "School roof collapsed, children trapped, severe bleeding, 3 injured people.",
            (77.6300, 12.9800),
        )
    ],
}


# Synthetic Medical ID the T+0 cardiac caller has opted in to share (CC-10). Values are
# invented; reads still need caller_is_patient = yes, an active incident and a reason (0008).
DEMO_PROFILE_REF = "mprof_syn_0001"
DEMO_PROFILE: dict[str, Any] = dict(
    consent_granted=True,
    scope=["conditions", "medications", "allergies"],
    conditions=["SYNTHETIC: prior angina"],
    medications=["SYNTHETIC: daily aspirin"],
    allergies=["SYNTHETIC: penicillin"],
    emergency_contacts=[],
    synthetic=True,
)


def seed_profile(session_id: str, incident_id: str) -> Callable[[sqlite3.Connection], None]:
    data = json.dumps(
        {**DEMO_PROFILE, "linked_incident_id": incident_id, "linked_session_id": session_id}
    )

    def write(conn: sqlite3.Connection) -> None:
        conn.execute(
            "INSERT INTO profiles VALUES (?, ?) ON CONFLICT(profile_ref) "
            "DO UPDATE SET data=excluded.data",
            (DEMO_PROFILE_REF, data),
        )

    return write


def preview(state: StateSnapshot, events: list[NewEvent]) -> StateSnapshot:
    for new in events:
        envelope: dict[str, Any] = dict(
            schema_version="1.0",
            session_id=state.session_id,
            sequence=state.as_of_sequence + 1,
            event_id=str(uuid.uuid4()),
            event_type=new.event_type,
            aggregate_type=new.aggregate_type,
            aggregate_id=new.aggregate_id,
            occurred_at="2026-09-30T00:00:00.000Z",
            sim_time_s=new.sim_time_s,
            actor={"kind": "system", "id": "preview"},
            correlation_id="preview",
            causation_id=None,
            idempotency_key=None,
            affects_planning=EVENT_CATALOG[new.event_type][0],
            payload=new.payload.model_dump(mode="json", by_alias=True),
        )
        state = apply(state, EVENT_ADAPTER.validate_python(envelope))
    return state


def advance(state: StateSnapshot, command: DemoAdvanceCommand) -> Decision:
    from app.api.operations import report_decision

    moment = STEPS[command.to_step]
    expected = (
        0 if not state.reports else next((s for s in STEPS.values() if s > state.sim_time_s), None)
    )
    if moment != expected:
        raise DomainError(409, "INVALID_TRANSITION", "Advance in order: T+0, T+2, T+5, T+10")
    writers = []
    events: list[NewEvent] = []
    working = state
    if moment == 120:
        a1 = next((u for u in working.units if u.unit_id == "unit_A1"), None)
        if a1 and a1.current_task and a1.status == "en_route":
            incident = next(
                i for i in working.incidents if i.incident_id == a1.current_task.incident_id
            )
            change = unit_status(
                working,
                a1.unit_id,
                UnitStatusCommand.model_validate(
                    dict(
                        expected_session_id=state.session_id,
                        to_status="on_scene",
                        position=incident.location,
                        sim_time_s=moment,
                    )
                ),
            )
            events.append(change)
            working = preview(working, [change])
    if moment == 600:
        for unit in working.units:
            if unit.unit_id == "unit_A2" and unit.status != "broken_down":
                change = unit_status(
                    working,
                    unit.unit_id,
                    UnitStatusCommand.model_validate(
                        dict(
                            expected_session_id=state.session_id,
                            to_status="broken_down",
                            sim_time_s=moment,
                        )
                    ),
                )
                events.append(change)
                working = preview(working, [change])
    if moment == 300:
        from app.contracts.commands import FloodEventCommand
        from app.domain.commands import flood_update

        change = flood_update(
            working,
            FloodEventCommand.model_validate(
                dict(
                    expected_session_id=state.session_id,
                    flood_id="flood_demo",
                    version=1,
                    closes_roads=True,
                    effective_sim_time_s=moment,
                    geometry={
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [77.615, 12.966],
                                [77.625, 12.966],
                                [77.625, 12.974],
                                [77.615, 12.974],
                                [77.615, 12.966],
                            ]
                        ],
                    },
                )
            ),
        )
        events.append(change)
        working = preview(working, [change])
    for text, coordinates in REPORTS[moment]:
        command_report = ReportCommand.model_validate(
            dict(
                expected_session_id=state.session_id,
                channel="text_sim",
                text=text,
                location={"type": "Point", "coordinates": coordinates},
                location_source="fixture",
                sim_time_s=moment,
            )
        )
        result = report_decision(working, command_report)
        if result.write_private:
            writers.append(result.write_private)
        if moment == 0 and text.startswith("Chest pain"):
            created = next(e for e in result.events if e.event_type == "IncidentCreated")
            writers.append(seed_profile(state.session_id, created.aggregate_id))
        events.extend(result.events)
        working = preview(working, result.events)
    # Shared tick advances time once for every unit, never one planning event per unit.
    events.append(
        NewEvent(
            "PlanningTickCommitted",
            "world",
            "tick",
            PlanningTickCommittedPayload(tick_sim_time_s=moment, units=[]),
            moment,
        )
    )

    def write_private(conn: sqlite3.Connection) -> None:
        for writer in writers:
            writer(conn)

    return Decision(
        events,
        lambda es: (200, dict(sim_time_s=moment, head_sequence=es[-1].sequence, appended=len(es))),
        write_private,
    )
