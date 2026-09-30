"""Route queries against the current world state (flood closures come from the projection)."""

from __future__ import annotations

from app.contracts.commands import RouteCandidate, RouteCandidates
from app.contracts.entities import Route
from app.contracts.state import StateSnapshot

from .geometry import Coord
from .graph import ROUTING_POLICY_VERSION, RoadGraph, load_default_graph
from .router import Closure, Router, flood_version

UNAVAILABLE_STATUSES = {"broken_down", "out_of_service", "off_duty"}


def active_closures(state: StateSnapshot) -> list[Closure]:
    """Road-closing flood zones in effect at the snapshot's simulation time."""
    return [
        Closure(
            f.flood_id,
            f.version,
            tuple(tuple((p[0], p[1]) for p in ring) for ring in f.geometry.coordinates),
        )
        for f in state.flood
        if f.closes_roads and f.effective_sim_time_s <= state.sim_time_s
    ]


class RouteService:
    def __init__(self, graph: RoadGraph | None = None) -> None:
        self.graph = graph or load_default_graph()
        self.router = Router(self.graph)

    def route(self, state: StateSnapshot, origin: Coord, destination: Coord) -> Route:
        return self.router.route(origin, destination, active_closures(state))

    def candidates(self, state: StateSnapshot, incident_id: str) -> RouteCandidates:
        """Fastest road route from every unit to an incident. Ordering is informational:
        eligibility and allocation remain the solver's job (0003)."""
        incident = next((i for i in state.incidents if i.incident_id == incident_id), None)
        if incident is None:
            raise KeyError(incident_id)
        closures = active_closures(state)
        rows = []
        for unit in state.units:
            route = self.router.route(
                unit.position.coordinates, incident.location.coordinates, closures
            )
            rows.append(
                RouteCandidate(
                    unit_id=unit.unit_id, unit_type=unit.type, unit_status=unit.status, route=route
                )
            )
        rows.sort(
            key=lambda r: (
                r.route.route_status != "ok",
                r.unit_status in UNAVAILABLE_STATUSES,
                r.route.duration_s if r.route.duration_s is not None else 0,
                r.unit_id,
            )
        )
        return RouteCandidates(
            session_id=state.session_id,
            incident_id=incident_id,
            as_of_sequence=state.as_of_sequence,
            flood_version=flood_version(closures),
            graph_version=self.graph.version,
            routing_policy_version=ROUTING_POLICY_VERSION,
            candidates=rows,
        )
