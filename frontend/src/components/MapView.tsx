import 'leaflet/dist/leaflet.css'
import { divIcon, type LatLngExpression } from 'leaflet'
import { useState } from 'react'
import { CircleMarker, MapContainer, Marker, Polygon, Polyline, TileLayer, Tooltip } from 'react-leaflet'
import type { Incident, Plan, Polygon as GeoPolygon, StateSnapshot } from '../contracts'
import { severityLabel, unitStatusLabel } from '../state/labels'

/** GeoJSON is [longitude, latitude]; Leaflet wants [latitude, longitude]. */
const ll = ([lon, lat]: number[]): LatLngExpression => [lat ?? 0, lon ?? 0]
const ring = (p: GeoPolygon): LatLngExpression[] => (p.coordinates[0] ?? []).map(ll)

export const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const CENTER: LatLngExpression = [12.965, 77.62]

const SEV_RADIUS: Record<string, number> = { critical: 11, high: 9, medium: 7, low: 6 }

interface MapViewProps {
  snapshot: StateSnapshot
  proposal: Plan | null
  selectedId: string | null
  onSelect: (id: string) => void
  /** Tiles are optional (offline demo); features and attribution render regardless. */
  tiles?: boolean
}

export function MapView({ snapshot, proposal, selectedId, onSelect, tiles = true }: MapViewProps) {
  const [tilesFailed, setTilesFailed] = useState(false)
  const uncovered = new Set(
    (proposal ?? snapshot.approved_plan)?.coverage.filter((c) => c.status !== 'covered').map((c) => c.zone_id) ?? [],
  )
  const incidents = snapshot.incidents.filter((i: Incident) => i.status === 'active')

  return (
    <section className="panel map-panel" aria-labelledby="map-title">
      <h2 id="map-title">Map</h2>
      <p className="visually-hidden">The map repeats the incident queue and fleet list, which are keyboard accessible.</p>
      {(tilesFailed || !tiles) && (
        <p className="notice" role="status">Map tiles unavailable — incidents, units and zones are shown without a base map.</p>
      )}
      <div className="map-frame">
        <MapContainer center={CENTER} zoom={12} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }} attributionControl>
          {tiles && !tilesFailed && (
            <TileLayer
              url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution={OSM_ATTRIBUTION}
              eventHandlers={{ tileerror: () => setTilesFailed(true) }}
            />
          )}
          {snapshot.reserve_zones.map((z) =>
            z.geometry ? (
              <Polygon
                key={z.zone_id}
                positions={ring(z.geometry)}
                pathOptions={{ color: '#6b7280', weight: 1, dashArray: uncovered.has(z.zone_id) ? '6 4' : undefined, fillOpacity: uncovered.has(z.zone_id) ? 0.12 : 0.03 }}
              >
                <Tooltip>{z.zone_id}{uncovered.has(z.zone_id) ? ' — UNCOVERED' : ' — covered'}</Tooltip>
              </Polygon>
            ) : null,
          )}
          {snapshot.flood.map((f) => (
            <Polygon key={f.flood_id} positions={ring(f.geometry)} pathOptions={{ color: '#1d4ed8', fillOpacity: 0.3 }}>
              <Tooltip>{f.flood_id} v{f.version}{f.closes_roads ? ' — roads closed' : ''}</Tooltip>
            </Polygon>
          ))}
          {snapshot.approved_plan?.assignments.map((a) =>
            a.route.geometry ? (
              <Polyline key={`approved-${a.assignment_id}`} positions={a.route.geometry.coordinates.map(ll)} pathOptions={{ color: '#374151', weight: 3 }} />
            ) : null,
          )}
          {proposal?.assignments.map((a) =>
            a.route.geometry ? (
              <Polyline key={`proposed-${a.assignment_id}`} positions={a.route.geometry.coordinates.map(ll)} pathOptions={{ color: '#b45309', weight: 3, dashArray: '8 6' }} />
            ) : null,
          )}
          {incidents.map((i) => (
            <CircleMarker
              key={i.incident_id}
              center={ll(i.location.coordinates)}
              radius={SEV_RADIUS[i.severity] ?? 6}
              pathOptions={{ color: i.incident_id === selectedId ? '#111827' : '#b91c1c', weight: i.incident_id === selectedId ? 4 : 2, fillOpacity: 0.6 }}
              eventHandlers={{ click: () => onSelect(i.incident_id) }}
            >
              <Tooltip permanent={i.incident_id === selectedId}>
                {severityLabel(i.severity)} · {i.incident_id}
              </Tooltip>
            </CircleMarker>
          ))}
          {snapshot.units.map((u) => (
            <Marker
              key={u.unit_id}
              position={ll(u.position.coordinates)}
              icon={divIcon({ className: `unit-marker unit-${u.status}`, html: `<span>${u.display_name}</span>`, iconSize: [30, 18] })}
              keyboard={false}
            >
              <Tooltip>{u.display_name} · {unitStatusLabel(u.status)}</Tooltip>
            </Marker>
          ))}
        </MapContainer>
      </div>
      <p className="map-legend muted">
        Solid line: approved route · dashed line: proposed route (not dispatched) · dashed zone: reserve uncovered · blue: flood
      </p>
    </section>
  )
}
