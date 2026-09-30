"""Intake session: facts from rules (+ optional model), targeted questions and human handoff.

Pure and deterministic given its inputs and an injected model. Emits contract
``TriageFacts``; escalation never depends on model success (0002).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.contracts.entities import TriageFacts

from .facts import (
    COUNT_FACTS,
    CRITICAL_FACTS,
    LIFE_THREAT,
    POLICY_VERSION,
    applicable_facts,
)
from .model_adapter import DEFAULT_TIMEOUT_S, FactModel, ModelUnavailableError, validate_model_facts
from .questions import Question, question_for
from .rules import RuleExtraction, extract

QUESTION_BUDGET = 2
INTAKE_TIME_LIMIT_S = 60

# Precedence of sources for a fact's final value.
_RANK = {"operator": 4, "caller_structured": 3, "model_adapter": 1, "rule_adapter": 1}


@dataclass
class _Fact:
    key: str
    value: str = "unknown"
    source: str = "rule_adapter"
    evidence: list[tuple[str, int, int]] = field(default_factory=list)  # (report_id, start, end)
    updated_sim_time_s: int = 0
    confirmed_by_operator: bool = False
    conflict: bool = False
    coerced_from: str | None = None
    coercion_reason: str | None = None


@dataclass
class _Count:
    value: int | None = None
    status: str = "unknown"
    source: str = "rule_adapter"
    evidence: list[tuple[str, int, int]] = field(default_factory=list)
    updated_sim_time_s: int = 0


@dataclass
class _Asked:
    fact_key: str
    asked_sim_time_s: int
    answer: str | None = None


@dataclass
class IntakeSession:
    incident_id: str
    model: FactModel | None = None
    model_timeout_s: float = DEFAULT_TIMEOUT_S
    started_sim_time_s: int | None = None
    kind: str = "unclassified_emergency"
    category: str = "emergency"
    language: str = "en"
    human_requested: bool = False
    injection_suspected: bool = False
    model_status: str = "not_configured"  # not_configured | ok | unavailable | ignored
    model_failure: str | None = None
    unclassified_critical_text: bool = False
    facts: dict[str, _Fact] = field(default_factory=dict)
    count: _Count = field(default_factory=_Count)
    asked: list[_Asked] = field(default_factory=list)
    report_ids: list[str] = field(default_factory=list)
    _escalated_at: int | None = None

    def __post_init__(self) -> None:
        for key in CRITICAL_FACTS:
            if key not in COUNT_FACTS:
                self.facts.setdefault(key, _Fact(key))

    # --- inputs -----------------------------------------------------------------------

    def add_report(self, report_id: str, text: str, sim_time_s: int) -> None:
        if self.started_sim_time_s is None:
            self.started_sim_time_s = sim_time_s
        self.report_ids.append(report_id)
        rules = extract(text)
        self._apply_rules(report_id, rules, sim_time_s)
        self._apply_model(report_id, text, rules, sim_time_s)

    def answer(self, fact_key: str, value: str, sim_time_s: int, *, operator: bool = False) -> None:
        """A structured Yes / No / Not sure answer (caller) or an operator confirmation."""
        if value not in ("yes", "no", "unknown"):
            raise ValueError("answers are yes, no or unknown")
        for q in reversed(self.asked):
            if q.fact_key == fact_key and q.answer is None:
                q.answer = value
                break
        if value == "unknown" and not operator:
            return  # "Not sure" keeps unknown and is recorded as asked (0002)
        source = "operator" if operator else "caller_structured"
        self.facts[fact_key] = _Fact(
            fact_key, value, source, [], sim_time_s, confirmed_by_operator=operator
        )

    def answer_count(
        self, value: int | None, sim_time_s: int, *, approximate: bool = False
    ) -> None:
        for q in reversed(self.asked):
            if q.fact_key == "people_count" and q.answer is None:
                q.answer = "unknown" if value is None else "yes"
                break
        if value is not None:
            self.count = _Count(
                value,
                "approximate" if approximate else "known",
                "caller_structured",
                [],
                sim_time_s,
            )

    def request_human(self) -> None:
        """The caller pressed 'Talk to a person'."""
        self.human_requested = True

    # --- questions and escalation -----------------------------------------------------

    def applicable(self) -> list[str]:
        observed = {k: f.value for k, f in self.facts.items()}
        return applicable_facts(self.kind, observed)

    def _unresolved(self) -> list[str]:
        out = []
        for key in self.applicable():
            if key in COUNT_FACTS:
                if self.count.status == "unknown":
                    out.append(key)
            elif self.facts[key].value == "unknown":
                out.append(key)
        return out

    def next_question(self, sim_time_s: int) -> Question | None:
        """Ask one targeted question: highest-priority unresolved applicable fact not yet asked."""
        if self.escalation_reasons(sim_time_s):
            return None  # an operator owns the conversation now
        asked = {q.fact_key for q in self.asked}
        for key in self._unresolved():
            if key not in asked:
                self.asked.append(_Asked(key, sim_time_s))
                return question_for(key, self.language)
        return None

    def escalation_reasons(self, sim_time_s: int) -> list[str]:
        reasons: list[str] = []
        if self.human_requested:
            reasons.append("CALLER_REQUESTED_HUMAN")
        if any(self.facts[k].value == v for k, v in LIFE_THREAT.items()):
            reasons.append("LIFE_THREAT_INDICATED")
        applicable = set(self.applicable())
        # "Not sure" answers, plus questions left unanswered when a later one was asked.
        outstanding = [q for q in self.asked if q.answer is None]
        superseded = outstanding[:-1]
        unresolved_answers = [
            q
            for q in [*superseded, *(q for q in self.asked if q.answer == "unknown")]
            if q.fact_key in applicable and self._still_unknown(q.fact_key)
        ]
        # Explicit None check: an intake that starts at T+0 must still hit the time limit.
        started = sim_time_s if self.started_sim_time_s is None else self.started_sim_time_s
        elapsed = sim_time_s - started
        if (
            self.category == "emergency"
            and self._unresolved()
            and (len(unresolved_answers) >= QUESTION_BUDGET or elapsed >= INTAKE_TIME_LIMIT_S)
        ):
            reasons.append("CRITICAL_UNCERTAINTY")
        if any(self.facts[k].conflict for k in applicable if k not in COUNT_FACTS):
            reasons.append("CONFLICTING_FACTS")
        if self.model_status != "ok" and self.unclassified_critical_text:
            reasons.append("MODEL_UNAVAILABLE_CRITICAL_TEXT")
        return reasons

    def _still_unknown(self, key: str) -> bool:
        return (
            self.count.status == "unknown"
            if key in COUNT_FACTS
            else self.facts[key].value == "unknown"
        )

    # --- output -----------------------------------------------------------------------

    def triage_facts(self, sim_time_s: int) -> TriageFacts:
        reasons = self.escalation_reasons(sim_time_s)
        if reasons and self._escalated_at is None:
            self._escalated_at = sim_time_s
        facts = []
        for key in CRITICAL_FACTS:
            if key in COUNT_FACTS:
                c = self.count
                facts.append(
                    {
                        "key": key,
                        "count": {"value": c.value, "status": c.status},
                        "source": c.source,
                        "evidence": [
                            {"report_id": r, "start": a, "end": b} for r, a, b in c.evidence
                        ],
                        "updated_sim_time_s": c.updated_sim_time_s,
                        "confirmed_by_operator": False,
                    }
                )
                continue
            f = self.facts[key]
            item: dict[str, object] = {
                "key": key,
                "value": f.value,
                "source": f.source,
                "evidence": [{"report_id": r, "start": a, "end": b} for r, a, b in f.evidence],
                "updated_sim_time_s": f.updated_sim_time_s,
                "confirmed_by_operator": f.confirmed_by_operator,
            }
            if f.conflict:
                item["conflict"] = True
            if f.coerced_from:
                item["coerced_from"] = f.coerced_from
                item["coercion_reason"] = f.coercion_reason
            facts.append(item)
        return TriageFacts.model_validate(
            {
                "incident_id": self.incident_id,
                "policy_version": POLICY_VERSION,
                "facts": facts,
                "applicable_facts": self.applicable(),
                "questions_asked": [
                    {
                        "fact_key": q.fact_key,
                        "asked_sim_time_s": q.asked_sim_time_s,
                        "answer": q.answer,
                    }
                    for q in self.asked
                ],
                "escalation": {
                    "escalated": bool(reasons),
                    "reasons": reasons,
                    "sim_time_s": self._escalated_at if reasons else None,
                },
            }
        )

    # --- internals --------------------------------------------------------------------

    def _apply_rules(self, report_id: str, rules: RuleExtraction, sim_time_s: int) -> None:
        first_report = len(self.report_ids) == 1
        if first_report:
            self.language = rules.language
            self.kind, self.category = rules.kind, rules.category
        elif rules.category == "emergency" and (
            self.category != "emergency" or self.kind == "unclassified_emergency"
        ):
            # Later messages may upgrade or refine; an emergency is never downgraded.
            self.kind, self.category = rules.kind, "emergency"
        self.human_requested |= rules.human_requested
        self.injection_suspected |= rules.injection_suspected
        self.unclassified_critical_text |= bool(rules.unclassified_critical_spans)
        for key, finding in rules.facts.items():
            current = self.facts[key]
            if _RANK.get(current.source, 0) > _RANK["rule_adapter"]:
                continue  # a caller/operator answer is not overridden by later free text
            spans = [(report_id, a, b) for a, b in finding.spans]
            if finding.conflict or (
                current.value not in ("unknown", finding.value) and current.evidence
            ):
                self.facts[key] = _Fact(
                    key,
                    "unknown",
                    "rule_adapter",
                    current.evidence + spans,
                    sim_time_s,
                    conflict=True,
                )
            else:
                self.facts[key] = _Fact(
                    key,
                    finding.value,
                    "rule_adapter",
                    current.evidence + spans,
                    sim_time_s,
                    conflict=current.conflict,
                )
        if (rules.count.status != "unknown" or rules.count.spans) and (
            self.count.source != "caller_structured"
        ):
            self.count = _Count(
                rules.count.value,
                rules.count.status,
                "rule_adapter",
                [(report_id, a, b) for a, b in rules.count.spans],
                sim_time_s,
            )

    def _apply_model(
        self, report_id: str, text: str, rules: RuleExtraction, sim_time_s: int
    ) -> None:
        if self.model is None:
            self.model_status = "not_configured"
            return
        if rules.injection_suspected:
            self.model_status, self.model_failure = "ignored", "PROMPT_INJECTION_SUSPECTED"
            return
        try:
            extraction = self.model.extract(text, timeout_s=self.model_timeout_s)
        except ModelUnavailableError as exc:
            self.model_status, self.model_failure = "unavailable", exc.cause
            return
        self.model_status, self.model_failure = "ok", None
        for vf in validate_model_facts(text, extraction):
            current = self.facts[vf.key]
            if current.source in ("operator", "caller_structured"):
                continue
            if vf.value == "unknown":
                if vf.coerced_from and current.value == "unknown" and not current.conflict:
                    self.facts[vf.key] = _Fact(
                        vf.key,
                        "unknown",
                        "model_adapter",
                        [],
                        sim_time_s,
                        coerced_from=vf.coerced_from,
                        coercion_reason=vf.coercion_reason,
                    )
                continue
            assert vf.span is not None
            span = (report_id, vf.span[0], vf.span[1])
            if current.value == "unknown" and not current.conflict:
                self.facts[vf.key] = _Fact(vf.key, vf.value, "model_adapter", [span], sim_time_s)
            elif current.value != vf.value and current.value != "unknown":
                # Rules and model disagree: keep it visible as a conflict (0002 rule 4).
                self.facts[vf.key] = _Fact(
                    vf.key,
                    "unknown",
                    "rule_adapter",
                    [*current.evidence, span],
                    sim_time_s,
                    conflict=True,
                )
