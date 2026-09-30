import type { StateSnapshot } from '../contracts'
import { simClock } from '../state/labels'

/** Current plan (proposal first) and derived situation, from server state only. */
function situation(snapshot: StateSnapshot) {
  const active = snapshot.incidents.filter((i) => i.category === 'emergency' && i.status === 'active')
  const plan = snapshot.current_proposal ?? snapshot.approved_plan
  const unmetCritical = plan?.unmet_needs.filter((n) => n.severity === 'critical').reduce((n, u) => n + u.quantity_unmet, 0) ?? 0
  const critical = active.filter((i) => i.severity === 'critical').length
  const status = unmetCritical > 0 ? 'CRITICAL_DEMAND_UNMET' : critical > 0 ? 'CRITICAL_RESPONDING' : active.length > 0 ? 'RESPONDING' : 'CLEAR'
  return { active, critical, unmetCritical, status }
}

/**
 * Data-strip header: city tag, the live emergency count as the hero figure, a bracketed
 * status derived from the plan, and a readout of session state. No decorative telemetry.
 */
export function CommandHeader({ snapshot }: { snapshot: StateSnapshot }) {
  const { active, critical, status } = situation(snapshot)
  return (
    <section className="command-header" aria-label="Operations overview">
      <div className="ds-left">
        <div className="ds-idline">
          <span className="ds-tag">BLR_01</span>
          <span className="ds-meta">CITY_RESPONSE // BENGALURU_METRO</span>
        </div>
        <div className="ds-hero">
          <span className="ds-big" aria-label={`${active.length} active emergencies`}>{String(active.length).padStart(2, '0')}</span>
          <span className="ds-hero-side">
            <span className="ds-chip" data-tone={status.startsWith('CRITICAL') ? 'alert' : 'ok'}>[ STATUS: {status} ]</span>
            <span className="ds-unit">ACTIVE_EMERGENCIES · {critical} CRITICAL</span>
          </span>
        </div>
      </div>
      <dl className="ds-readout">
        <div><dt>SIM_TIME</dt><dd>{simClock(snapshot.sim_time_s)}</dd></div>
        <div><dt>EVENT_SEQ</dt><dd>#{String(snapshot.as_of_sequence).padStart(5, '0')}</dd></div>
        <div><dt>SESSION</dt><dd>{snapshot.session_id}</dd></div>
        <div><dt>DISPATCH</dt><dd>HUMAN_APPROVAL · SIMULATED</dd></div>
      </dl>
    </section>
  )
}

/** Red strip when critical demand is unmet in the current plan; neutral otherwise. */
export function CommandFooter({ snapshot }: { snapshot: StateSnapshot }) {
  const { unmetCritical } = situation(snapshot)
  const plan = snapshot.current_proposal ?? snapshot.approved_plan
  const unreachable = plan?.unmet_needs.some((n) => n.reasons.some((r) => r.code === 'NO_REACHABLE_UNIT')) ?? false
  return (
    <footer className={`command-footer${unmetCritical > 0 ? ' ds-alert' : ''}`} role={unmetCritical > 0 ? 'status' : undefined}>
      {unmetCritical > 0 ? (
        <span>
          <span className="ds-blink" aria-hidden="true" /> ALERT: {unmetCritical}_CRITICAL_NEED{unmetCritical === 1 ? '' : 'S'}_UNMET
          {unreachable ? ' · SOME_UNREACHABLE_BY_ROAD' : ''} — REVIEW PLAN
        </span>
      ) : (
        <span>CRISIS_COMMAND // SIMULATION_ENVIRONMENT</span>
      )}
      <span>{snapshot.session_id} / SYNTHETIC_DATA</span>
    </footer>
  )
}
