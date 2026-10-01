import 'maplibre-gl/dist/maplibre-gl.css'
import {
  AttributionControl,
  LngLatBounds,
  Map as MapLibreMap,
  Marker,
  NavigationControl,
  type GeoJSONSource,
  type StyleSpecification,
} from 'maplibre-gl'
import type { FeatureCollection, LineString, Polygon as GeoPolygon } from 'geojson'
import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import type { Incident, Plan, Route, StateSnapshot, Unit } from '../contracts'
import { severityLabel, unitStatusLabel } from '../state/labels'
import type { Theme } from '../state/theme'
import { IncidentKindIcon, UnitTypeIcon } from './icons'

/** Free, key-less vector styles (OpenFreeMap, OpenStreetMap data); attribution comes from the style. */
const STYLE_URLS: Record<Theme, string> = {
  dark: 'https://tiles.openfreemap.org/styles/dark',
  light: 'https://tiles.openfreemap.org/styles/positron',
}

const CENTER: [number, number] = [77.62, 12.965]

function blankStyle(theme: Theme): StyleSpecification {
  return {
    version: 8,
    sources: {},
    layers: [{ id: 'background', type: 'background', paint: { 'background-color': theme === 'dark' ? '#1C2127' : '#E5E8EB' } }],
  }
}

function styleTacticalBasemap(map: MapLibreMap, theme: Theme): void {
  if (theme !== 'dark') return
  // Only style provider base layers, before operational overlays are added.
  for (const layer of map.getStyle().layers) {
    const sourceLayer = 'source-layer' in layer ? layer['source-layer'] : ''
    if (layer.type === 'background') map.setPaintProperty(layer.id, 'background-color', '#151717')
    if (layer.type === 'fill') {
      map.setPaintProperty(layer.id, 'fill-color', sourceLayer === 'water' ? '#101313' : '#1b1e1c')
    }
    if (layer.type === 'line' && sourceLayer === 'transportation') {
      map.setPaintProperty(layer.id, 'line-color', layer.id.includes('casing') ? '#202321' : '#3b423c')
    }
    if (layer.type === 'symbol' && layer.layout?.['text-field']) {
      map.setPaintProperty(layer.id, 'text-color', '#929b90')
      map.setPaintProperty(layer.id, 'text-halo-color', '#151717')
    }
  }
}


export interface CandidateRoute {
  unitId: string
  route: Route
}

function overlays(
  snapshot: StateSnapshot,
  proposal: Plan | null,
  candidates: CandidateRoute[],
  focusedUnitId: string | null,
): Record<string, FeatureCollection> {
  const coverage = (proposal ?? snapshot.approved_plan)?.coverage ?? []
  const uncovered = new Set(coverage.filter((c) => c.status !== 'covered').map((c) => c.zone_id))
  const routes = (plan: Plan | null | undefined): FeatureCollection => ({
    type: 'FeatureCollection',
    features: (plan?.assignments ?? [])
      .filter((a) => a.route.geometry && a.eta_s > 0)
      .map((a) => ({ type: 'Feature', properties: { unit: a.unit_id }, geometry: a.route.geometry as LineString })),
  })
  return {
    zones: {
      type: 'FeatureCollection',
      features: snapshot.reserve_zones
        .filter((z) => z.geometry)
        .map((z) => ({ type: 'Feature', properties: { id: z.zone_id, uncovered: uncovered.has(z.zone_id) }, geometry: z.geometry as GeoPolygon })),
    },
    flood: {
      type: 'FeatureCollection',
      features: snapshot.flood.map((f) => ({ type: 'Feature', properties: { id: f.flood_id }, geometry: f.geometry as GeoPolygon })),
    },
    approved: routes(snapshot.approved_plan),
    proposed: routes(proposal),
    candidates: {
      type: 'FeatureCollection',
      features: candidates
        .filter((c) => c.route.route_status === 'ok' && c.route.geometry)
        .map((c) => ({
          type: 'Feature',
          properties: { unit: c.unitId, focused: c.unitId === focusedUnitId },
          geometry: c.route.geometry as LineString,
        })),
    },
  }
}

function addOverlayLayers(map: MapLibreMap, data: Record<string, FeatureCollection>, theme: Theme): void {
  for (const [id, fc] of Object.entries(data)) {
    const existing = map.getSource(id) as GeoJSONSource | undefined
    if (existing) existing.setData(fc)
    else map.addSource(id, { type: 'geojson', data: fc })
  }
  if (map.getLayer('zones-line')) return
  const dark = theme === 'dark'
  if (map.getSource('openmaptiles') && !map.getLayer('buildings-3d')) {
    map.addLayer({
      id: 'buildings-3d',
      type: 'fill-extrusion',
      source: 'openmaptiles',
      'source-layer': 'building',
      minzoom: 12.5,
      paint: {
        'fill-extrusion-color': dark ? '#2F343C' : '#D3D8DE',
        'fill-extrusion-height': ['coalesce', ['get', 'render_height'], 8],
        'fill-extrusion-base': ['coalesce', ['get', 'render_min_height'], 0],
        'fill-extrusion-opacity': dark ? 0.85 : 0.7,
      },
    })
  }
  map.addLayer({ id: 'zones-fill', type: 'fill', source: 'zones', filter: ['==', ['get', 'uncovered'], true], paint: { 'fill-color': '#EC9A3C', 'fill-opacity': 0.08 } })
  map.addLayer({
    id: 'zones-line', type: 'line', source: 'zones',
    paint: {
      'line-color': ['case', ['get', 'uncovered'], '#EC9A3C', dark ? '#5F6B7C' : '#8F99A8'],
      'line-width': ['case', ['get', 'uncovered'], 1.5, 1],
      'line-dasharray': [4, 3],
    },
  })
  map.addLayer({ id: 'flood-fill', type: 'fill', source: 'flood', paint: { 'fill-color': '#4C90F0', 'fill-opacity': 0.28 } })
  map.addLayer({ id: 'flood-line', type: 'line', source: 'flood', paint: { 'line-color': '#4C90F0', 'line-width': 1.5 } })
  map.addLayer({ id: 'routes-approved', type: 'line', source: 'approved', layout: { 'line-cap': 'round' }, paint: { 'line-color': dark ? '#C5CBD3' : '#404854', 'line-width': 2, 'line-opacity': 0.9 } })
  map.addLayer({ id: 'routes-proposed-casing', type: 'line', source: 'proposed', paint: { 'line-color': dark ? '#111418' : '#ffffff', 'line-width': 5, 'line-opacity': 0.7 } })
  map.addLayer({ id: 'routes-proposed', type: 'line', source: 'proposed', paint: { 'line-color': '#EC9A3C', 'line-width': 2, 'line-dasharray': [2, 2] } })
  // Road-router candidates for the selected incident: faint alternatives, one focused route.
  map.addLayer({ id: 'candidates-alt', type: 'line', source: 'candidates', filter: ['!', ['get', 'focused']], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#B9ABD2', 'line-width': 1.5, 'line-opacity': 0.35 } })
  map.addLayer({ id: 'candidates-casing', type: 'line', source: 'candidates', filter: ['get', 'focused'], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': dark ? '#0a0d12' : '#ffffff', 'line-width': 7, 'line-opacity': 0.85 } })
  map.addLayer({ id: 'candidates-focus', type: 'line', source: 'candidates', filter: ['get', 'focused'], layout: { 'line-cap': 'round', 'line-join': 'round' }, paint: { 'line-color': '#B9ABD2', 'line-width': 3.5 } })
}

const DASH_STEPS: [number, number, number][] = [
  [0, 2, 2], [0.5, 2, 1.5], [1, 2, 1], [1.5, 2, 0.5], [2, 2, 0],
]

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

const fmtLat = (v: number) => `${Math.abs(v).toFixed(4)}°${v >= 0 ? 'N' : 'S'}`
const fmtLng = (v: number) => `${Math.abs(v).toFixed(4)}°${v >= 0 ? 'E' : 'W'}`
const fmtDeg = (v: number) => `${String(Math.round(((v % 360) + 360) % 360)).padStart(3, '0')}°`

function IncidentPin({ incident, selected }: { incident: Incident; selected: boolean }) {
  return (
    <div className={`pin sev-${incident.severity}${selected ? ' selected' : ''}`} aria-hidden="true">
      {incident.severity === 'critical' && <span className="pin-ring" />}
      {selected && <span className="pin-bracket" />}
      <span className="pin-shape">
        <span className="pin-glyph"><IncidentKindIcon kind={incident.kind} size={11} strokeWidth={2.4} /></span>
      </span>
      <span className="pin-label mono">
        {incident.incident_id.toUpperCase()} · {severityLabel(incident.severity)}
      </span>
    </div>
  )
}

function UnitChip({ unit }: { unit: Unit }) {
  return (
    <div className={`unit-chip unit-${unit.status}`} aria-hidden="true" title={`${unit.display_name} · ${unitStatusLabel(unit.status)}`}>
      <UnitTypeIcon type={unit.type} size={11} strokeWidth={2.2} />
      <span className="mono">{unit.display_name}</span>
    </div>
  )
}

interface MapViewProps {
  snapshot: StateSnapshot
  proposal: Plan | null
  /** Road-router routes for the selected incident (informational layer). */
  candidates?: CandidateRoute[]
  focusedUnitId?: string | null
  selectedId: string | null
  onSelect: (id: string) => void
  theme: Theme
  /** Vector base map on/off (tests, offline demos). Features render regardless. */
  tiles?: boolean
}

export function MapView({ snapshot, proposal, candidates = [], focusedUnitId = null, selectedId, onSelect, theme, tiles = true }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const markersRef = useRef(new Map<string, Marker>())
  const fittedRef = useRef(false)
  const [markerEls, setMarkerEls] = useState<Record<string, HTMLElement>>({})
  const [baseMapFailed, setBaseMapFailed] = useState(false)
  const [hud, setHud] = useState({ lng: CENTER[0], lat: CENTER[1], zoom: 11.4, bearing: -12, pitch: 20 })
  const [cursor, setCursor] = useState<{ lng: number; lat: number } | null>(null)
  const data = useMemo(
    () => overlays(snapshot, proposal, candidates, focusedUnitId),
    [snapshot, proposal, candidates, focusedUnitId],
  )
  const dataRef = useRef(data)
  const themeRef = useRef(theme)
  const onSelectRef = useRef(onSelect)
  useEffect(() => {
    dataRef.current = data
    themeRef.current = theme
    onSelectRef.current = onSelect
  })

  // Create the map once.
  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const map = new MapLibreMap({
      container,
      style: tiles ? STYLE_URLS[themeRef.current] : blankStyle(themeRef.current),
      center: CENTER,
      zoom: 11.4,
      // A gentle tilt: steep pitch pulls tiles out to the horizon and slows first load.
      pitch: 20,
      bearing: -12,
      maxPitch: 60,
      // Stay on Bengaluru so the map never fetches tiles for far-away areas.
      maxBounds: [
        [77.25, 12.7],
        [78.0, 13.25],
      ],
      minZoom: 9.5,
      attributionControl: false,
      fadeDuration: 0,
    })
    map.addControl(new AttributionControl({ compact: false }), 'bottom-right')
    map.addControl(new NavigationControl({ showCompass: true, visualizePitch: true }), 'bottom-right')
    let styleLoadedOnce = false
    map.on('style.load', () => {
      styleLoadedOnce = true
      styleTacticalBasemap(map, themeRef.current)
      addOverlayLayers(map, dataRef.current, themeRef.current)
    })
    // A missing style server must not hide incidents: if the base style never loads,
    // switch to a blank style. Later transient tile errors keep the loaded style.
    const fallback = () => {
      if (styleLoadedOnce) return
      styleLoadedOnce = true
      setBaseMapFailed(true)
    }
    map.on('error', fallback)
    const styleTimeout = setTimeout(fallback, 8000)
    // HUD: camera and cursor readouts, throttled to animation frames.
    let hudFrame = 0
    const readCamera = () => {
      cancelAnimationFrame(hudFrame)
      hudFrame = requestAnimationFrame(() => {
        const c = map.getCenter()
        setHud({ lng: c.lng, lat: c.lat, zoom: map.getZoom(), bearing: map.getBearing(), pitch: map.getPitch() })
      })
    }
    map.on('move', readCamera)
    map.on('mousemove', (e: { lngLat: { lng: number; lat: number } }) => setCursor({ lng: e.lngLat.lng, lat: e.lngLat.lat }))
    map.on('mouseout', () => setCursor(null))
    let frame = 0
    let step = 0
    let last = 0
    const animate = (time: number) => {
      if (time - last > 90 && map.getLayer('routes-proposed')) {
        step = (step + 1) % DASH_STEPS.length
        map.setPaintProperty('routes-proposed', 'line-dasharray', DASH_STEPS[step])
        last = time
      }
      frame = requestAnimationFrame(animate)
    }
    if (!prefersReducedMotion() && typeof requestAnimationFrame === 'function') frame = requestAnimationFrame(animate)
    mapRef.current = map
    // Keep the canvas matched to its panel when the layout changes (e.g. expanded map).
    const resizer =
      typeof ResizeObserver === 'function' ? new ResizeObserver(() => map.resize()) : null
    resizer?.observe(container)
    const markers = markersRef.current
    return () => {
      resizer?.disconnect()
      clearTimeout(styleTimeout)
      cancelAnimationFrame(frame)
      cancelAnimationFrame(hudFrame)
      markers.forEach((m) => m.remove())
      markers.clear()
      map.remove()
      mapRef.current = null
    }
    // The map instance lives for the component's lifetime; theme/data updates are applied below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Theme or base-map changes swap the style; overlays are re-added on style.load.
  const styleKey = `${theme}-${tiles && !baseMapFailed}`
  const firstStyle = useRef(styleKey)
  useEffect(() => {
    const map = mapRef.current
    if (!map || firstStyle.current === styleKey) return
    firstStyle.current = styleKey
    map.setStyle(tiles && !baseMapFailed ? STYLE_URLS[theme] : blankStyle(theme))
  }, [styleKey, tiles, baseMapFailed, theme])

  // Keep overlay data current. Not gated on isStyleLoaded(): that is false while any base
  // tile is loading, which silently dropped live updates (a dispatched plan kept its
  // "proposed" routes). Sources missing mid style swap are added from dataRef on style.load.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    for (const [id, fc] of Object.entries(data)) (map.getSource(id) as GeoJSONSource | undefined)?.setData(fc)
  }, [data])

  // Sync DOM markers (positions are MapLibre's; contents are rendered by React below).
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const markers = markersRef.current
    const wanted = new Map<string, [number, number]>()
    for (const i of snapshot.incidents) if (i.status === 'active') wanted.set(`incident:${i.incident_id}`, i.location.coordinates)
    for (const u of snapshot.units) wanted.set(`unit:${u.unit_id}`, u.position.coordinates)
    let changed = false
    for (const [key, marker] of markers) {
      if (!wanted.has(key)) {
        marker.remove()
        markers.delete(key)
        changed = true
      }
    }
    for (const [key, lngLat] of wanted) {
      const existing = markers.get(key)
      if (existing) {
        existing.setLngLat(lngLat)
        continue
      }
      const element = document.createElement('div')
      element.className = key.startsWith('incident:') ? 'marker marker-incident' : 'marker marker-unit'
      if (key.startsWith('incident:')) {
        const id = key.slice('incident:'.length)
        element.addEventListener('click', () => onSelectRef.current(id))
      }
      markers.set(key, new Marker({ element, anchor: 'center' }).setLngLat(lngLat).addTo(map))
      changed = true
    }
    if (changed) setMarkerEls(Object.fromEntries([...markers].map(([k, m]) => [k, m.getElement()])))
    if (!fittedRef.current && wanted.size > 0) {
      const bounds = new LngLatBounds()
      wanted.forEach((c) => bounds.extend(c))
      map.fitBounds(bounds, { padding: { top: 70, bottom: 70, left: 60, right: 60 }, maxZoom: 13, duration: 0, pitch: 20, bearing: -12 })
      fittedRef.current = true
    }
  }, [snapshot.incidents, snapshot.units])

  // Bring the selected incident into view above the triage sheet.
  const selectedCoords = snapshot.incidents.find((i) => i.incident_id === selectedId)?.location.coordinates
  const selectedLng = selectedCoords?.[0]
  const selectedLat = selectedCoords?.[1]
  useEffect(() => {
    const map = mapRef.current
    if (!map || selectedLng == null || selectedLat == null) return
    // Opening the detail dock shrinks the map; a resize mid-animation cancels the ease,
    // so resize first and start the camera move on the next frame.
    const frame = requestAnimationFrame(() => {
      map.resize()
      map.easeTo({
        center: [selectedLng, selectedLat],
        zoom: Math.max(map.getZoom(), 13.2),
        padding: { top: 90, bottom: 40, left: 40, right: 40 },
        duration: prefersReducedMotion() ? 0 : 800,
      })
    })
    return () => cancelAnimationFrame(frame)
  }, [selectedLng, selectedLat])

  const incidents = new Map(snapshot.incidents.map((i) => [i.incident_id, i]))
  const units = new Map(snapshot.units.map((u) => [u.unit_id, u]))

  return (
    <section className="map-panel" aria-labelledby="map-title">
      <h2 id="map-title" className="visually-hidden">Map</h2>
      <p className="visually-hidden">The map repeats the incident queue and fleet list, which are keyboard accessible.</p>
      <div ref={containerRef} className="map-canvas" data-testid="map-canvas" />
      {Object.entries(markerEls).map(([key, element]) => {
        const [kind, id = ''] = key.split(':')
        if (kind === 'incident') {
          const incident = incidents.get(id)
          return incident ? createPortal(<IncidentPin incident={incident} selected={id === selectedId} />, element, key) : null
        }
        const unit = units.get(id)
        return unit ? createPortal(<UnitChip unit={unit} />, element, key) : null
      })}
      {(baseMapFailed || !tiles) && (
        <p className="map-notice" role="status">Base map unavailable — incidents, units and zones are shown without it.</p>
      )}
      <div className="map-frame" aria-hidden="true" />
      <div className="hud hud-top" aria-hidden="true">
        <div className="hud-row">
          <span className="kv-label">Cam</span>
          <span className="mono">{fmtLat(hud.lat)} {fmtLng(hud.lng)}</span>
        </div>
        <div className="hud-row">
          <span className="kv-label">Z</span>
          <span className="mono">{hud.zoom.toFixed(1)}</span>
          <span className="kv-label">Brg</span>
          <span className="mono">{fmtDeg(hud.bearing)}</span>
          <span className="kv-label">Tilt</span>
          <span className="mono">{Math.round(hud.pitch)}°</span>
        </div>
        <div className="hud-row">
          <span className="kv-label">Cursor</span>
          <span className="mono">{cursor ? `${fmtLat(cursor.lat)} ${fmtLng(cursor.lng)}` : '—'}</span>
        </div>
      </div>
      <div className="map-legend" aria-hidden="true">
        <span className="kv-label">Legend</span>
        <span><i className="lg-line lg-approved" />Approved route</span>
        <span><i className="lg-line lg-proposed" />Proposed · not dispatched</span>
        {candidates.length > 0 && <span><i className="lg-line lg-road" />Road route · router</span>}
        <span><i className="lg-box lg-flood" />Flood zone</span>
        <span><i className="lg-box lg-uncovered" />Reserve uncovered</span>
      </div>
    </section>
  )
}
