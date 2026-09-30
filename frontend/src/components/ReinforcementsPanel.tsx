import type { RouteCandidatesView } from '../api/types'
import { formatSeconds, unitStatusLabel, unitTypeLabel } from '../state/labels'
import { UnitTypeIcon } from './icons'

const NOT_TASKABLE = new Set(['broken_down', 'out_of_service', 'off_duty'])

const UNAVAILABLE_TEXT: Record<string, string> = {
  DESTINATION_IN_CLOSED_FLOOD_ZONE: 'Destination inside a closed flood zone',
  ORIGIN_IN_CLOSED_FLOOD_ZONE: 'Unit inside a closed flood zone',
  ORIGIN_NOT_NEAR_OPEN_ROAD: 'Unit not near an open road',
  DESTINATION_NOT_NEAR_OPEN_ROAD: 'Incident not near an open road',
  NO_OPEN_ROAD_PATH: 'No open road path',
}

const km = (m: number | null | undefined) => (m == null ? '—' : `${(m / 1000).toFixed(1)} km`)

interface ReinforcementsPanelProps {
  state: { status: 'idle' | 'loading' | 'error' } | { status: 'ready'; data: RouteCandidatesView }
  focusedUnitId: string | null
  onFocus: (unitId: string | null) => void
  snapshotSequence: number
}

/**
 * Fastest road route from every unit to the selected incident, as computed by the road
 * router. Informational: it ranks by road ETA only; the plan (solver) decides assignments.
 */
export function ReinforcementsPanel({ state, focusedUnitId, onFocus, snapshotSequence }: ReinforcementsPanelProps) {
  return (
    <section className="reinforcements" aria-labelledby="reinf-title">
      <h2 id="reinf-title" className="section-title">
        Reinforcements by road
        <span className="section-hint">fastest road route · not an allocation</span>
      </h2>
      {state.status === 'idle' && <p className="empty">Select an incident to compute road routes.</p>}
      {state.status === 'loading' && <p className="empty" aria-busy="true">Computing road routes…</p>}
      {state.status === 'error' && <p className="notice notice-error">Road routes unavailable. The plan is unaffected.</p>}
      {state.status === 'ready' && (
        <>
          <table className="grid-table reinf-table">
            <thead>
              <tr>
                <th scope="col">Unit</th>
                <th scope="col">Status</th>
                <th scope="col" className="num">Road ETA</th>
                <th scope="col" className="num">Distance</th>
              </tr>
            </thead>
            <tbody>
              {state.data.candidates.map((c, rank) => {
                const ok = c.route.route_status === 'ok'
                const taskable = !NOT_TASKABLE.has(c.unit_status)
                const focused = c.unit_id === focusedUnitId
                return (
                  <tr key={c.unit_id} className={`${focused ? 'focused' : ''}${!ok || !taskable ? ' dim' : ''}`}>
                    <th scope="row">
                      <button
                        type="button"
                        className="row-button mono"
                        aria-pressed={focused}
                        disabled={!ok}
                        onClick={() => onFocus(focused ? null : c.unit_id)}
                        aria-label={`${c.unit_id.replace('unit_', '')}: ${ok ? `road ETA ${formatSeconds(c.route.duration_s)}` : 'no road route'}. Show on map`}
                      >
                        <span className="rank">{ok && taskable ? rank + 1 : '–'}</span>
                        <UnitTypeIcon type={c.unit_type} size={13} />
                        {c.unit_id.replace('unit_', '')}
                        <span className="muted"> {unitTypeLabel(c.unit_type)}</span>
                      </button>
                    </th>
                    <td><span className={`status st-${c.unit_status}`}>{unitStatusLabel(c.unit_status)}</span></td>
                    {ok ? (
                      <>
                        <td className="num mono">{formatSeconds(c.route.duration_s)}</td>
                        <td className="num mono">{km(c.route.distance_m)}</td>
                      </>
                    ) : (
                      <td colSpan={2} className="unavail">{UNAVAILABLE_TEXT[c.route.unavailable_reason ?? ''] ?? c.route.unavailable_reason}</td>
                    )}
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="provenance mono">
            router {state.data.graph_version} · {state.data.routing_policy_version} · flood v{state.data.flood_version} · as of seq{' '}
            {state.data.as_of_sequence}
            {state.data.as_of_sequence !== snapshotSequence && <span className="stale-note"> · recorded before the current state</span>}
          </p>
        </>
      )}
    </section>
  )
}
