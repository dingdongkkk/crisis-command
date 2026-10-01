"""Canonical contract models (single source of truth; see docs/decisions/0001-0009).

JSON Schema, OpenAPI and TypeScript consumers are generated from these models by
``python -m app.contracts.export`` and ``npm run gen:contracts``; never hand-edit them.
"""

from typing import Any

from pydantic import TypeAdapter

from . import commands, common, entities, plan, state
from .common import SCHEMA_VERSION, Problem, in_demo_bounds
from .events import EVENT_ADAPTER, EVENT_CATALOG

# Named top-level contracts. Keys are the stable names used by fixtures, JSON Schema
# ``$defs`` and generated TypeScript.
CONTRACT_MODELS: dict[str, Any] = {
    "Report": entities.Report,
    "TriageFact": entities.TriageFact,
    "TriageFacts": entities.TriageFacts,
    "Incident": entities.Incident,
    "Unit": entities.Unit,
    "Hospital": entities.Hospital,
    "Shelter": entities.Shelter,
    "FloodZone": entities.FloodZone,
    "ReserveZone": entities.ReserveZone,
    "Route": entities.Route,
    "Override": entities.Override,
    "MedicalProfileConsent": entities.MedicalProfileConsent,
    "Assignment": plan.Assignment,
    "PolicyFlag": plan.PolicyFlag,
    "PlanDiff": plan.PlanDiff,
    "Plan": plan.Plan,
    "Policy": state.Policy,
    "DispatchCommand": state.DispatchCommand,
    "StateSnapshot": state.StateSnapshot,
    "Problem": common.Problem,
    "ReportCommand": commands.ReportCommand,
    "AnswerCommand": commands.AnswerCommand,
    "FactConfirmCommand": commands.FactConfirmCommand,
    "DuplicateResolveCommand": commands.DuplicateResolveCommand,
    "MedicalProfileAccessCommand": commands.MedicalProfileAccessCommand,
    "UnitStatusCommand": commands.UnitStatusCommand,
    "FloodEventCommand": commands.FloodEventCommand,
    "RecomputeCommand": commands.RecomputeCommand,
    "ApproveCommand": commands.ApproveCommand,
    "OverrideCommand": commands.OverrideCommand,
    "DemoResetCommand": commands.DemoResetCommand,
    "DemoAdvanceCommand": commands.DemoAdvanceCommand,
    "HealthResponse": commands.HealthResponse,
    "ReportAccepted": commands.ReportAccepted,
    "UnitStatusAccepted": commands.UnitStatusAccepted,
    "FloodAccepted": commands.FloodAccepted,
    "RecomputeAccepted": commands.RecomputeAccepted,
    "ApprovalAccepted": commands.ApprovalAccepted,
    "OverrideRecorded": commands.OverrideRecorded,
    "DemoResetResult": commands.DemoResetResult,
    "DemoAdvanceResult": commands.DemoAdvanceResult,
    "WsSubscribe": commands.WsSubscribe,
    "RouteCandidates": commands.RouteCandidates,
}

ADAPTERS: dict[str, TypeAdapter[Any]] = {
    name: TypeAdapter(model) for name, model in CONTRACT_MODELS.items()
}
ADAPTERS["EventEnvelope"] = EVENT_ADAPTER
ADAPTERS["WsServerMessage"] = TypeAdapter(commands.WsServerMessage)

__all__ = [
    "ADAPTERS",
    "CONTRACT_MODELS",
    "EVENT_ADAPTER",
    "EVENT_CATALOG",
    "SCHEMA_VERSION",
    "Problem",
    "in_demo_bounds",
]
