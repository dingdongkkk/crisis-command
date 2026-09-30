# CC-07: Codex verification and routing completion work

- Existing implementation: Claude PR #19, commit a6808f4; integrated unchanged before extensions.
- Branch: `codex/cc-07-routing-completion`, stacked on CC-05.
- Status: partial, ready for review; water navigation remains unavailable.

Verified the existing road/closure/cache tests. Added optional ORS Directions with bounded requests, metre/second conversion, invalid-response rejection, polygon intersection validation, and a cache keyed by request plus flood versions. API key is server-side only. Timeouts/errors have no ETA. Tests use an HTTP mock; no live ORS call or quota claim was made.

The allocator now checks onward routes and facility capacity. `RouteService.boat_route` explicitly returns `WATER_ROUTE_NOT_CONFIGURED`; a road ETA can never become a boat ETA. Unknown/over-capacity passenger counts are ineligible. A verified water graph or an explicitly approved synthetic water-access fixture is still required to complete boat navigation. No invented water corridor was added.

ORS contract references: https://giscience.github.io/openrouteservice/api-reference/endpoints/directions/routing-options and https://giscience.github.io/openrouteservice/v9.10.0/api-reference/endpoints/directions/requests-and-return-types.
