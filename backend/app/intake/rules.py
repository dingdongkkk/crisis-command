"""Deterministic rule adapter: phrases -> tri-state facts with character-span evidence.

Always runs, needs no network or key, and never asserts a value without the span that
supports it. Contradictory phrases for one fact yield ``unknown`` with ``conflict``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .facts import CRITICAL_FACTS, DANGEROUS_VALUE, LIFE_THREAT
from .lexicon import (
    COUNT_PATTERN,
    COUNT_UNKNOWN,
    CRITICAL_KEYWORDS,
    FACT_PATTERNS,
    HUMAN_REQUEST,
    INJECTION_MARKERS,
    KIND_RULES,
    parse_number,
)

Span = tuple[int, int]


@dataclass(frozen=True)
class FactFinding:
    key: str
    value: str  # "yes" | "no" | "unknown"
    spans: tuple[Span, ...] = ()
    conflict: bool = False


@dataclass(frozen=True)
class CountFinding:
    value: int | None
    status: str  # "known" | "approximate" | "unknown"
    spans: tuple[Span, ...] = ()


@dataclass
class RuleExtraction:
    facts: dict[str, FactFinding] = field(default_factory=dict)
    count: CountFinding = CountFinding(None, "unknown")
    kind: str = "unclassified_emergency"
    category: str = "emergency"
    kind_spans: tuple[Span, ...] = ()
    human_requested: bool = False
    human_spans: tuple[Span, ...] = ()
    injection_suspected: bool = False
    unclassified_critical_spans: tuple[Span, ...] = ()
    language: str = "en"


def _matches(patterns: tuple[re.Pattern[str], ...], text: str) -> list[Span]:
    return [m.span() for p in patterns for m in p.finditer(text)]


def _contained(inner: Span, outers: list[Span]) -> bool:
    return any(o[0] <= inner[0] and inner[1] <= o[1] and o != inner for o in outers)


def detect_language(text: str) -> str:
    if re.search(r"[ऀ-ॿ]", text):
        return "hi"
    hinglish = re.findall(
        r"\b(?:hai|hain|nahi|nahin|kya|mein|raha|rahi|rahe|bhai|jaldi|bachao|paani|aag|log|koi|kuch|abhi|"
        r"gir|gaya|gayi|saans|khoon|dard|seene|behosh|pata|kitne|baat)\b",
        text,
        re.IGNORECASE,
    )
    return "hinglish" if len(hinglish) >= 2 else "en"


def extract(text: str) -> RuleExtraction:
    out = RuleExtraction(language=detect_language(text))

    for key in CRITICAL_FACTS:
        if key == "people_count":
            continue
        yes = _matches(FACT_PATTERNS[key].get("yes", ()), text)
        no = _matches(FACT_PATTERNS[key].get("no", ()), text)
        # A "no" phrase that contains a "yes" phrase (e.g. "no fire" ⊃ "fire") overrides it.
        yes = [s for s in yes if not _contained(s, no)]
        no = [s for s in no if not _contained(s, yes)]
        if yes and no:
            out.facts[key] = FactFinding(key, "unknown", tuple(sorted(yes + no)), conflict=True)
        elif yes:
            out.facts[key] = FactFinding(key, "yes", tuple(sorted(yes)))
        elif no:
            out.facts[key] = FactFinding(key, "no", tuple(sorted(no)))

    counts = [m for m in COUNT_PATTERN.finditer(text)]
    unknown_count = _matches(COUNT_UNKNOWN, text)
    if counts and not unknown_count:
        values = [(parse_number(m.group("num")), bool(m.group("approx")), m.span()) for m in counts]
        values = [v for v in values if v[0] is not None]
        if values:
            number = max(v[0] for v in values if v[0] is not None)
            approx = any(v[1] for v in values) or len({v[0] for v in values}) > 1
            out.count = CountFinding(
                number, "approximate" if approx else "known", tuple(v[2] for v in values)
            )
    elif unknown_count:
        out.count = CountFinding(None, "unknown", tuple(unknown_count))

    for rule in KIND_RULES:
        spans = _matches(rule.patterns, text)
        if spans:
            out.kind, out.category, out.kind_spans = rule.kind, rule.category, tuple(spans)
            break

    out.human_spans = tuple(_matches(HUMAN_REQUEST, text))
    out.human_requested = bool(out.human_spans)
    out.injection_suspected = bool(_matches(INJECTION_MARKERS, text))

    evidence = (
        [s for f in out.facts.values() for s in f.spans]
        + list(out.kind_spans)
        + list(out.count.spans)
    )
    out.unclassified_critical_spans = tuple(
        s
        for s in _matches(CRITICAL_KEYWORDS, text)
        if not any(e[0] <= s[0] and s[1] <= e[1] for e in evidence)
    )
    # Non-routine signals override a routine category. A breakdown upgrades on any danger
    # (e.g. water rising around a stuck car). An information request is a question about
    # the road, so road-condition words alone ("is ORR flooded?") do not upgrade it; a life
    # threat, someone trapped, the caller in danger or fire does.
    observed = {k: f.value for k, f in out.facts.items()}
    upgrade_keys = {
        "non_emergency_assist": set(DANGEROUS_VALUE),
        "information_request": set(LIFE_THREAT) | {"caller_in_danger", "fire_or_smoke"},
    }.get(out.category, set())
    if any(observed.get(k) == DANGEROUS_VALUE[k] for k in upgrade_keys):
        # Re-classify into the best-matching emergency kind (e.g. flood-stranded vehicle).
        emergency = next(
            (r for r in KIND_RULES if r.category == "emergency" and _matches(r.patterns, text)),
            None,
        )
        out.kind = emergency.kind if emergency else "unclassified_emergency"
        out.category = "emergency"
        if emergency:
            out.kind_spans = tuple(_matches(emergency.patterns, text))
    return out
