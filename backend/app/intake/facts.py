"""Critical fact catalogue: order, polarity and applicability (0002, policy demo-2026.2)."""

from __future__ import annotations

POLICY_VERSION = "demo-2026.2"

# Question/priority order: life signs, then hazards, then counts (0002 question policy).
CRITICAL_FACTS: tuple[str, ...] = (
    "conscious",
    "breathing_normally",
    "chest_pain",
    "severe_bleeding",
    "trapped",
    "fire_or_smoke",
    "gas_smell",
    "water_rising",
    "caller_in_danger",
    "people_count",
)
COUNT_FACTS = frozenset({"people_count"})

# Value that indicates danger; the other binary value is the "safe" (risk-lowering) one.
DANGEROUS_VALUE: dict[str, str] = {
    "conscious": "no",
    "breathing_normally": "no",
    "chest_pain": "yes",
    "severe_bleeding": "yes",
    "trapped": "yes",
    "fire_or_smoke": "yes",
    "gas_smell": "yes",
    "water_rising": "yes",
    "caller_in_danger": "yes",
}
LIFE_THREAT: dict[str, str] = {
    "breathing_normally": "no",
    "conscious": "no",
    "chest_pain": "yes",
    "severe_bleeding": "yes",
    "trapped": "yes",
}

LIFE_SIGNS = ("conscious", "breathing_normally")
APPLICABLE_BY_KIND: dict[str, tuple[str, ...]] = {
    "cardiac_chest_pain": (*LIFE_SIGNS, "chest_pain", "severe_bleeding", "people_count"),
    "medical_emergency": (*LIFE_SIGNS, "chest_pain", "severe_bleeding", "people_count"),
    "road_accident_injuries": (
        *LIFE_SIGNS,
        "severe_bleeding",
        "trapped",
        "fire_or_smoke",
        "people_count",
    ),
    "structural_collapse": (*LIFE_SIGNS, "trapped", "fire_or_smoke", "people_count"),
    "gas_leak_evacuation": ("gas_smell", "fire_or_smoke", "caller_in_danger", "people_count"),
    "flood_stranded_vehicle": ("water_rising", "trapped", "caller_in_danger", "people_count"),
    "fire": (*LIFE_SIGNS, "fire_or_smoke", "trapped", "people_count"),
    # Ambiguous possible emergency: provisional life signs plus handoff (0002).
    "unclassified_emergency": (*LIFE_SIGNS, "people_count"),
    # Road information and explicitly non-injury roadside reports: patient facts do not apply.
    "information_request": (),
    "vehicle_breakdown": (),
}


def safe_value(key: str) -> str:
    return "yes" if DANGEROUS_VALUE[key] == "no" else "no"


def applicable_facts(kind: str, observed: dict[str, str]) -> list[str]:
    """Facts that apply to this report, in priority order.

    The kind's set, plus any critical fact observed with a dangerous value (evidence of a
    casualty or hazard makes it applicable).
    """
    base = set(APPLICABLE_BY_KIND.get(kind, APPLICABLE_BY_KIND["unclassified_emergency"]))
    for key, value in observed.items():
        if key in DANGEROUS_VALUE and value == DANGEROUS_VALUE[key]:
            base.add(key)
            if key in LIFE_THREAT:
                base.update(LIFE_SIGNS)  # a casualty makes life signs relevant
    return [k for k in CRITICAL_FACTS if k in base]
