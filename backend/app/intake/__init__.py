"""Typed text intake (CC-06): rule adapter, optional model adapter, questions, handoff.

Default operation uses only the deterministic rule adapter (no network, no API key).
"""

from .explain import accept_rewrite, explain_triage
from .model_adapter import FactModel, GeminiAdapter, ModelExtraction, ModelUnavailableError
from .questions import Question
from .session import IntakeSession

__all__ = [
    "FactModel",
    "GeminiAdapter",
    "IntakeSession",
    "ModelExtraction",
    "ModelUnavailableError",
    "Question",
    "accept_rewrite",
    "explain_triage",
]
