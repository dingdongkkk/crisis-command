"""Versioned demonstration assessment. Unknowns retain their polarity and provenance."""

from app.contracts.common import ReasonFact
from app.contracts.entities import Incident, Need, TriageFacts
from app.contracts.enums import IncidentCategory, NeedBasis, NeedType, Severity
from app.contracts.state import Policy


def assess(incident: Incident, facts: TriageFacts, policy: Policy) -> Incident:
    if facts.policy_version != policy.policy_version:
        raise ValueError("assessment policy mismatch")
    values = {f.key: f.value for f in facts.facts}
    dangerous = {
        k
        for k in facts.applicable_facts
        if k in policy.dangerous_values
        and values.get(k, "unknown") in ("unknown", policy.dangerous_values[k])
    }
    unknown = sorted(k for k in dangerous if values.get(k, "unknown") == "unknown")
    needs: list[Need] = []
    category = incident.category
    # A road-status question ("is the underpass flooded?") names a hazard without reporting
    # one; like the intake rules, only fire or a caller in danger upgrades it. Life threats
    # were already upgraded by intake. Other routine categories upgrade on any hazard.
    upgrade = (
        ("fire_or_smoke", "caller_in_danger")
        if category == IncidentCategory.INFORMATION_REQUEST
        else ("water_rising", "fire_or_smoke", "gas_smell", "caller_in_danger")
    )
    if any(values.get(k) == "yes" for k in upgrade):
        category = IncidentCategory.EMERGENCY

    def add(kind: NeedType, quantity: int, keys: set[str]) -> None:
        if quantity < 1:
            return
        provisional = bool(keys) and all(k in unknown for k in keys)
        needs.append(
            Need(
                need_id=f"{incident.incident_id}_{kind.value}",
                type=kind,
                quantity=quantity,
                basis=NeedBasis.PROVISIONAL_UNKNOWN if provisional else NeedBasis.CONFIRMED,
                reasons=[
                    ReasonFact(
                        code="CRITICAL_UNKNOWN" if provisional else "FACT_INDICATED",
                        params={"fact_keys": sorted(keys)},
                    )
                ],
            )
        )

    severity = Severity.LOW
    if category == IncidentCategory.EMERGENCY:
        life = dangerous & {"conscious", "breathing_normally", "chest_pain", "severe_bleeding"}
        severity = Severity.HIGH
        if life:
            severity = Severity.CRITICAL
            add(NeedType.ALS, 1, life)
        if incident.kind in ("school_roof_collapse", "structural_collapse"):
            severity = Severity.CRITICAL
            add(NeedType.BLS, 2, set())
        elif incident.kind in ("road_accident", "injury_accident", "road_accident_injuries"):
            add(NeedType.BLS, 1, set())
        if (
            dangerous & {"fire_or_smoke", "gas_smell", "trapped"}
            and "water_rising" not in dangerous
        ):
            add(NeedType.FIRE, 1, dangerous & {"fire_or_smoke", "gas_smell", "trapped"})
        if "water_rising" in dangerous:
            add(NeedType.WATER_RESCUE, 1, {"water_rising"})
        count = next((f.count for f in facts.facts if f.key == "people_count"), None)
        if "gas_smell" in dangerous and count and count.value:
            add(NeedType.SHELTER_PLACES, count.value, {"gas_smell"})
    return incident.model_copy(
        update={
            "category": category,
            "severity": severity,
            "assumed_facts": unknown,
            "needs": needs,
        }
    )
