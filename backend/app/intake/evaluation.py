"""Triage evaluation against labelled multilingual cases (evals/triage/*.jsonl).

Counts, per fact, how predictions compare with expectations. The safety metric is
``unsafe_downgrades``: a critical fact predicted at its *safe* value when the text does not
establish that value. It must be zero. Zero observed misses on a small synthetic set is not
a guarantee on real calls.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .facts import CRITICAL_FACTS, DANGEROUS_VALUE, safe_value
from .model_adapter import FactModel
from .session import IntakeSession


@dataclass
class CaseResult:
    id: str
    lang: str
    family: str
    errors: list[str] = field(default_factory=list)
    unsafe_downgrades: list[str] = field(default_factory=list)


@dataclass
class Report:
    dataset: str
    cases: int = 0
    passed: int = 0
    unsafe_downgrades: int = 0
    missed_danger: int = 0
    false_danger: int = 0
    category_correct: int = 0
    escalations_required: int = 0
    escalations_met: int = 0
    by_lang: Counter[str] = field(default_factory=Counter)
    failures: list[CaseResult] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset,
            "cases": self.cases,
            "passed": self.passed,
            "unsafe_downgrades": self.unsafe_downgrades,
            "missed_danger": self.missed_danger,
            "false_danger": self.false_danger,
            "category_accuracy": f"{self.category_correct}/{self.cases}",
            "required_escalations_met": f"{self.escalations_met}/{self.escalations_required}",
            "cases_by_language": dict(self.by_lang),
            "failures": [{"id": f.id, "lang": f.lang, "errors": f.errors} for f in self.failures],
        }


def load_cases(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def evaluate(path: Path, model: FactModel | None = None) -> Report:
    report = Report(dataset=path.name)
    for case in load_cases(path):
        report.cases += 1
        report.by_lang[case["lang"]] += 1
        result = CaseResult(case["id"], case["lang"], case["family"])
        session = IntakeSession(f"inc_{case['id']}", model=model)
        session.add_report(f"rpt_{case['id']}", case["text"], 0)
        facts = {f.key: f for f in session.triage_facts(0).facts}
        expect = case["expect"]

        for key in CRITICAL_FACTS:
            wanted = expect["facts"].get(key, "unknown")
            fact = facts[key]
            if key == "people_count":
                got: Any = (
                    fact.count.value
                    if fact.count and fact.count.status.value == "known"
                    else (
                        f"~{fact.count.value}"
                        if fact.count and fact.count.status.value == "approximate"
                        else "unknown"
                    )
                )
                if got != wanted:
                    result.errors.append(f"{key}: expected {wanted}, got {got}")
                continue
            got = "conflict" if fact.conflict else (fact.value.value if fact.value else "unknown")
            if got != wanted:
                result.errors.append(f"{key}: expected {wanted}, got {got}")
            dangerous, safe = DANGEROUS_VALUE[key], safe_value(key)
            if got == safe and wanted != safe:
                result.unsafe_downgrades.append(key)
            if wanted == dangerous and got != dangerous:
                report.missed_danger += 1
            if got == dangerous and wanted != dangerous:
                report.false_danger += 1

        if session.category == expect["category"]:
            report.category_correct += 1
        else:
            result.errors.append(f"category: expected {expect['category']}, got {session.category}")
        reasons = set(session.escalation_reasons(0))
        for reason in expect["escalation"]:
            report.escalations_required += 1
            if reason in reasons:
                report.escalations_met += 1
            else:
                result.errors.append(f"escalation: missing {reason}")

        report.unsafe_downgrades += len(result.unsafe_downgrades)
        if result.errors:
            report.failures.append(result)
        else:
            report.passed += 1
    return report
