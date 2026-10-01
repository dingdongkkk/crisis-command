"""Contract tests: every CC-01 example validates, every negative fails with its code."""

from __future__ import annotations

import json
import re
from typing import Any

import pytest

from app.contracts import ADAPTERS, EVENT_ADAPTER, EVENT_CATALOG
from app.contracts.entities import Incident, Unit
from app.contracts.plan import Plan
from app.contracts.state import Policy, StateSnapshot
from app.contracts.validation import fixture_errors, plan_world_errors, schema_errors
from tests.fixtures import load, materialise

ENTITY_MODELS = {
    "Report": "Report",
    "TriageFacts": "TriageFacts",
    "Incident": "Incident",
    "Unit": "Unit",
    "Hospital": "Hospital",
    "Shelter": "Shelter",
    "FloodZone": "FloodZone",
    "ReserveZone": "ReserveZone",
    "Route": "Route",
    "RouteUnavailable": "Route",
    "BridgeAssignment": "Assignment",
    "Override": "Override",
    "MedicalProfileConsent": "MedicalProfileConsent",
}

# (method, path regex) -> request model name
COMMANDS = [
    ("POST", r"^/reports$", "ReportCommand"),
    ("POST", r"^/units/[^/]+/status$", "UnitStatusCommand"),
    ("POST", r"^/flood-events$", "FloodEventCommand"),
    ("POST", r"^/plans/recompute$", "RecomputeCommand"),
    ("POST", r"^/plans/[^/]+/approve$", "ApproveCommand"),
    ("POST", r"^/overrides$", "OverrideCommand"),
    ("POST", r"^/incidents/[^/]+/medical-profile-access$", "MedicalProfileAccessCommand"),
    ("POST", r"^/demo/reset$", "DemoResetCommand"),
    ("POST", r"^/demo/advance$", "DemoAdvanceCommand"),
]
SUCCESS_RESPONSES = {
    "health": "HealthResponse",
    "state_snapshot": "StateSnapshot",
    "get_plan": "Plan",
    "post_report_valid": "ReportAccepted",
    "post_report_geographically_valid_outside_demo": "ReportAccepted",
    "unit_status_valid": "UnitStatusAccepted",
    "flood_event_valid": "FloodAccepted",
    "recompute": "RecomputeAccepted",
    "approve_valid": "ApprovalAccepted",
    "approve_idempotent_retry": "ApprovalAccepted",
    "override_bls_bridge_valid": "OverrideRecorded",
    "demo_reset": "DemoResetResult",
    "demo_reset_idempotent_retry": "DemoResetResult",
    "demo_advance": "DemoAdvanceResult",
}
# Request bodies that the API must reject at schema level, with the expected code.
INVALID_REQUEST_BODIES = {"flood_event_unclosed_ring": "POLYGON_RING_INVALID"}

API = load("api.examples.json")
WORLD = StateSnapshot.model_validate(load("world.before.json"))
POLICY = Policy.model_validate(load("policy.valid.json"))


def _command_model(method: str, path: str) -> str:
    for m, pattern, name in COMMANDS:
        if m == method and re.match(pattern, path.split("?")[0]):
            return name
    raise AssertionError(f"no command model for {method} {path}")


@pytest.mark.parametrize("key", sorted(ENTITY_MODELS))
def test_entity_examples_validate(key: str) -> None:
    assert schema_errors(ENTITY_MODELS[key], load("entities.valid.json")[key]) == set()


def test_plan_policy_and_world_validate() -> None:
    assert schema_errors("Plan", load("plan.valid.json")) == set()
    assert schema_errors("Policy", load("policy.valid.json")) == set()
    assert WORLD.policy == POLICY


def test_plan_passes_world_invariants() -> None:
    plan = Plan.model_validate(load("plan.valid.json"))
    incidents = [*WORLD.incidents, Incident.model_validate(load("entities.valid.json")["Incident"])]
    assert plan_world_errors(plan, WORLD.units, incidents, POLICY) == set()


@pytest.mark.parametrize(
    "event", load("events.valid.json"), ids=lambda e: f"{e['sequence']}-{e['event_type']}"
)
def test_event_examples_validate(event: dict[str, Any]) -> None:
    parsed = EVENT_ADAPTER.validate_python(event)
    assert parsed.affects_planning == EVENT_CATALOG[event["event_type"]][0]


def test_event_catalog_matches_decision_0005() -> None:
    planning = {name for name, (affects, _) in EVENT_CATALOG.items() if affects}
    assert "PlanningTickCommitted" in planning and "SessionStarted" in planning
    assert "UnitPositionObserved" not in planning and "PlanProposed" not in planning


def test_affects_planning_is_fixed_by_catalog() -> None:
    event = dict(load("events.valid.json")[0])
    event["affects_planning"] = not event["affects_planning"]
    assert schema_errors("EventEnvelope", event) == {"AFFECTS_PLANNING_MISMATCH"}


def test_unknown_event_type_rejected() -> None:
    event = dict(load("events.valid.json")[0], event_type="PlanDispatchedForReal")
    assert schema_errors("EventEnvelope", event)


@pytest.mark.parametrize("case", API, ids=lambda c: c["name"])
def test_api_examples(case: dict[str, Any]) -> None:
    request, response = case["request"], case["response"]
    if request["method"] == "POST":
        errors = schema_errors(_command_model(request["method"], request["path"]), request["body"])
        assert errors == (
            {INVALID_REQUEST_BODIES[case["name"]]}
            if case["name"] in INVALID_REQUEST_BODIES
            else set()
        )
    body = response.get("body")
    if response["status"] >= 400:
        assert schema_errors("Problem", body) == set()
        assert body["status"] == response["status"]
    else:
        assert schema_errors(SUCCESS_RESPONSES[case["name"]], body) == set()


def test_every_success_response_is_covered() -> None:
    success = {c["name"] for c in API if c["response"]["status"] < 400}
    assert success == set(SUCCESS_RESPONSES)


@pytest.mark.parametrize("case", load("schema.invalid.json"), ids=lambda c: c["name"])
def test_negative_cases_fail_with_named_error(case: dict[str, Any]) -> None:
    layer, entity = case["validation_layer"], case["entity"]

    def errors(value: Any) -> set[str]:
        if layer == "fixture":
            return fixture_errors(Unit.model_validate(value).position)
        schema = schema_errors(entity, value)
        if layer == "schema" or schema or entity != "Plan":
            return schema
        plan = Plan.model_validate(value)
        incidents = [
            *WORLD.incidents,
            Incident.model_validate(load("entities.valid.json")["Incident"]),
        ]
        return plan_world_errors(plan, WORLD.units, incidents, POLICY)

    assert errors(materialise(case, patched=False)) == set(), "unpatched base must be valid"
    assert errors(materialise(case)) == {case["expected_error"]}


def test_all_named_contracts_have_adapters() -> None:
    for name in ["EventEnvelope", "WsServerMessage", "Plan", "StateSnapshot", "Problem"]:
        assert name in ADAPTERS


def test_exported_schema_uses_only_real_keywords() -> None:
    """Regression: validator ordering once leaked `ge`/`le` and untyped coordinates."""
    from app.contracts.export import build_schema

    text = json.dumps(build_schema())
    assert '"ge":' not in text and '"le":' not in text
    point = build_schema()["$defs"]["Point"]["properties"]["coordinates"]
    assert point["items"] == {"type": "number"} and point["minItems"] == point["maxItems"] == 2
    assert point["prefixItems"][0]["maximum"] == 180 and point["prefixItems"][1]["maximum"] == 90
