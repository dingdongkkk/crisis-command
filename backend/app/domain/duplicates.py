"""Spatial/time blocking only; candidates never silently merge distinct incidents."""

from app.contracts.entities import Incident
from app.contracts.state import StateSnapshot
from app.routing.geometry import haversine_m


def duplicate_candidates(state: StateSnapshot, incident: Incident) -> list[str]:
    return sorted(
        i.incident_id
        for i in state.incidents
        if i.status == "active"
        and i.category == incident.category
        and i.incident_id != incident.incident_id
        and abs(i.created_sim_time_s - incident.created_sim_time_s) <= 300
        and haversine_m(i.location.coordinates, incident.location.coordinates) <= 150
    )
