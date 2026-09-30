"""Operator explanations derived only from validated facts (0002, CC-06 acceptance 3).

Templates restate a validated ``TriageFacts`` snapshot. Any optional model rewrite must pass
``accept_rewrite``: it may rephrase but may not introduce numbers or identifiers that are
not present in the source facts; otherwise the template text is kept.
"""

from __future__ import annotations

import json
import re

from app.contracts.entities import TriageFacts

FACT_NAMES = {
    "conscious": "Conscious",
    "breathing_normally": "Breathing normally",
    "chest_pain": "Chest pain",
    "severe_bleeding": "Severe bleeding",
    "trapped": "Trapped",
    "fire_or_smoke": "Fire or smoke",
    "gas_smell": "Gas smell",
    "water_rising": "Water rising",
    "caller_in_danger": "Caller in danger",
    "people_count": "People involved",
}
REASONS = {
    "CALLER_REQUESTED_HUMAN": "caller asked for a person",
    "LIFE_THREAT_INDICATED": "life threat indicated",
    "CRITICAL_UNCERTAINTY": "critical facts still unknown after questions",
    "CONFLICTING_FACTS": "sources disagree on a critical fact",
    "MODEL_UNAVAILABLE_CRITICAL_TEXT": "unclassified critical wording, no model available",
}
SOURCES = {
    "caller_structured": "caller answer",
    "rule_adapter": "rules",
    "model_adapter": "language model",
    "operator": "operator",
    "medical_profile": "medical profile",
}


def explain_triage(facts: TriageFacts) -> list[str]:
    lines: list[str] = []
    if facts.escalation.escalated:
        lines.append(
            "Escalated to operator: "
            + "; ".join(REASONS.get(r, r) for r in facts.escalation.reasons)
            + "."
        )
    applicable = set(facts.applicable_facts)
    unknown: list[str] = []
    for f in facts.facts:
        name = FACT_NAMES.get(f.key, f.key)
        if f.count is not None:
            if f.count.status == "unknown":
                if f.key in applicable:
                    unknown.append(name)
            else:
                qualifier = " (approximate)" if f.count.status == "approximate" else ""
                lines.append(
                    f"{name}: {f.count.value}{qualifier} — {SOURCES[f.source]}{_where(f)}."
                )
            continue
        if f.conflict:
            lines.append(f"{name}: sources disagree — kept UNKNOWN until confirmed{_where(f)}.")
        elif f.value is not None and f.value.value != "unknown":
            lines.append(f"{name}: {f.value.value.upper()} — {SOURCES[f.source]}{_where(f)}.")
        elif f.key in applicable:
            unknown.append(name)
        if f.coerced_from is not None:
            lines.append(
                f"{name}: language model said {f.coerced_from.value.upper()} "
                "without supporting words; kept UNKNOWN."
            )
    if unknown:
        lines.append(
            "Not established (treated as present for planning): " + ", ".join(unknown) + "."
        )
    return lines


def _where(fact: object) -> str:
    evidence = getattr(fact, "evidence", [])
    if not evidence:
        return ""
    return " (" + ", ".join(f"{e.report_id} chars {e.start}-{e.end}" for e in evidence) + ")"


_TOKEN = re.compile(r"\b(?:[a-z]+_[A-Za-z0-9_]+|\d+(?:\.\d+)?)\b")


def grounded_tokens(facts: TriageFacts) -> set[str]:
    return set(_TOKEN.findall(json.dumps(facts.model_dump(mode="json"))))


def ungrounded(text: str, facts: TriageFacts) -> set[str]:
    """Numbers and identifiers in ``text`` that the validated facts do not contain."""
    return set(_TOKEN.findall(text)) - grounded_tokens(facts)


def accept_rewrite(template: str, rewrite: str | None, facts: TriageFacts) -> str:
    """Use a model's rephrasing only if it adds no numbers/IDs; otherwise keep the template."""
    if not rewrite or ungrounded(rewrite, facts) or len(rewrite) > 4 * max(len(template), 40):
        return template
    return rewrite
