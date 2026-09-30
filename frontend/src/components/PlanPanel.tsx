import { CircleCheck, CircleDashed, Clock, OctagonAlert, Send } from 'lucide-react'
import { forwardRef } from 'react'
import type { Assignment, DiffRow, Incident, Plan } from '../contracts'
import type { PlanView } from '../state/planView'
import { requiredAcks, unrecognisedValues } from '../state/planView'
import type { PlanAction } from '../state/useConsole'
import {
  flagSeverityLabel,
  flagSubject,
  formatSeconds,
  lockLabel,
  needTypeLabel,
  reasonText,
  severityIcon,
  severityLabel,
} from '../state/labels'

interface PlanPanelProps {
  view: PlanView
  incidents: Incident[]
  action: PlanAction
  acked: string[]
  commandsEnabled: boolean
  onAck: (planId: string, flagId: string, checked: boolean) => void
  onApprove: () => void
  onOverride: (prefill?: { kind: 'approve_bls_bridge'; unitId: string; needId: string }) => void
  onDismissNotice: () => void
  approveRef: React.Ref<HTMLButtonElement>
}

function headerText(view: PlanView, action: PlanAction): string {
  if (action.kind === 'approving' && 'plan' in view) return `Approving v${view.plan.version}…`
  if (action.kind === 'busy_retrying') return `Server busy — retrying approval (attempt ${action.attempt + 1})…`
  switch (view.kind) {
    case 'no_plan':
      return view.approved ? `No proposal. Approved plan v${view.approved.version} in force.` : 'No proposal and no approved plan.'
    case 'computing':
      return `Computing plan…${view.approved ? ` Approved plan v${view.approved.version} remains in force.` : ''}`
    case 'proposed':
      return `PROPOSED v${view.plan.version} — not dispatched`
    case 'stale':
      return `STALE v${view.plan.version} — world changed since this plan was computed. Recomputing.`
    case 'approved':
      return `APPROVED v${view.plan.version} — dispatch queued (simulated)`
    case 'dispatched':
      return `DISPATCHED (simulated) v${view.plan.version}`
    case 'partial_failed':
      return `DISPATCH PARTIALLY FAILED (simulated) v${view.plan.version}`
    case 'unrecognised':
      return `Unrecognised plan state (${view.state}) — cannot be approved here`
  }
}

function statusIcon(view: PlanView) {
  switch (view.kind) {
    case 'proposed':
      return <CircleDashed size={16} />
    case 'stale':
    case 'partial_failed':
    case 'unrecognised':
      return <OctagonAlert size={16} />
    case 'approved':
      return <Send size={16} />
    case 'dispatched':
      return <CircleCheck size={16} />
    default:
      return <Clock size={16} />
  }
}

function AssignmentRow({ a }: { a: Assignment }) {
  const bridge = a.role === 'bridge'
  return (
    <li className={bridge ? 'bridge' : undefined}>
      <strong>{a.unit_id}</strong> → {a.incident_id} · {bridge ? `BLS bridge for ${a.bridges_need_id ?? '?'} — not ALS care. ALS still unmet.` : a.need_id}
      {' · '}ETA {formatSeconds(a.eta_s)}
      {a.locked && <span className="tag">LOCKED: {lockLabel(a.locked)}</span>}
      <details>
        <summary>Why</summary>
        <ul>{a.reasons.map((r, i) => <li key={i}>{reasonText(r)}</li>)}</ul>
      </details>
    </li>
  )
}

function DiffRows({ title, rows, render }: { title: string; rows: DiffRow[]; render: (r: DiffRow) => string }) {
  if (rows.length === 0) return null
  return (
    <div className="diff-group">
      <h4>{title} ({rows.length})</h4>
      <ul>
        {rows.map((r) => (
          <li key={`${title}-${r.unit_id}`}>
            {render(r)}
            {r.reason && <span className="muted"> — {reasonText(r.reason)}</span>}
          </li>
        ))}
      </ul>
    </div>
  )
}

function PlanBody({ plan, view, incidents, acked, onAck, onOverride, editable }: {
  plan: Plan
  incidents: Incident[]
  view: PlanView
  acked: string[]
  onAck: PlanPanelProps['onAck']
  onOverride: PlanPanelProps['onOverride']
  editable: boolean
}) {
  const diff = plan.diff
  const changedUnits = new Set([...diff.changed, ...diff.added, ...diff.released].map((r) => r.unit_id))
  const unchanged = plan.assignments.filter((a) => !changedUnits.has(a.unit_id))
  const showAcks = view.kind === 'proposed'

  return (
    <>
      <p className="muted solver">
        Solver {plan.solver.status}
        {!plan.solver.lexicographic_complete && ' · time limit reached, not proven optimal'} · {plan.solver.wall_time_ms} ms · based on seq{' '}
        {plan.based_on_planning_sequence} · policy {plan.policy_version}
      </p>

      {plan.flags.length > 0 && (
        <div className="flags">
          <h3>Flags</h3>
          <ul>
            {plan.flags.map((f) => {
              const id = `ack-${f.flag_id}`
              const subject = flagSubject(f, incidents)
              return (
                <li key={f.flag_id} className={`flag flag-${f.severity}`}>
                  <span className="flag-sev">{flagSeverityLabel(f.severity)}</span> {f.message}
                  {subject && <span className="flag-subject">{subject}</span>}
                  {f.requires_ack && showAcks && (
                    <label htmlFor={id} className="ack">
                      <input
                        id={id}
                        type="checkbox"
                        checked={acked.includes(f.flag_id)}
                        disabled={!editable}
                        onChange={(e) => onAck(plan.plan_id, f.flag_id, e.target.checked)}
                      />{' '}
                      I understand: {f.message}{subject ? ` — ${subject}` : ''}
                    </label>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      )}

      {plan.unmet_needs.length > 0 && (
        <div className="unmet">
          <h3>Unmet needs ({plan.unmet_needs.length})</h3>
          <ul>
            {plan.unmet_needs.map((n) => (
              <li key={n.need_id}>
                <span className={`sev-badge sev-${n.severity}`}>
                  <span aria-hidden="true">{severityIcon(n.severity)} </span>
                  {severityLabel(n.severity)}
                </span>{' '}
                {needTypeLabel(n.type)} ×{n.quantity_unmet} at {n.incident_id}
                {n.basis === 'provisional_unknown' && <span className="tag tag-provisional">PROVISIONAL</span>}
                <span className="muted"> · waiting {formatSeconds(n.waiting_s)}</span>
                <div className="why-not">
                  <strong>Why not:</strong>
                  <ul>{n.reasons.map((r, i) => <li key={i}>{reasonText(r)}</li>)}</ul>
                </div>
                {n.type === 'als' && n.bridge_candidates && n.bridge_candidates.length > 0 && (
                  <div className="bridges">
                    <strong>BLS bridge candidates (not ALS care):</strong>
                    <ul>
                      {n.bridge_candidates.map((c) => (
                        <li key={c.unit_id}>
                          {c.unit_id} · ETA {formatSeconds(c.eta_s)}
                          {c.cost_of_taking.length > 0 && (
                            <span className="muted">
                              {' '}· cost: {c.cost_of_taking.map((x) => `${x.metric.replaceAll('_', ' ')}${x.need_id ? ` ${x.need_id}` : ''}`).join(', ')}
                            </span>
                          )}{' '}
                          <button
                            type="button"
                            disabled={!editable}
                            onClick={() => onOverride({ kind: 'approve_bls_bridge', unitId: c.unit_id, needId: n.need_id })}
                          >
                            Propose BLS bridge…
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="diff">
        <h3>Changes versus {diff.against_plan_id ?? 'no approved plan'}</h3>
        <DiffRows title="Changed" rows={diff.changed} render={(r) => `${r.unit_id}: ${r.from.incident_id ?? r.from.state ?? '—'} → ${r.to?.incident_id ?? '—'} (ETA ${formatSeconds(r.to?.eta_s)})`} />
        <DiffRows title="New" rows={diff.added} render={(r) => `${r.unit_id}: ${r.from.state ?? '—'}${r.from.zone_id ? ` in ${r.from.zone_id}` : ''} → ${r.to?.incident_id ?? '—'} (ETA ${formatSeconds(r.to?.eta_s)})`} />
        <DiffRows title="Released" rows={diff.released} render={(r) => `${r.unit_id}: released from ${r.from.incident_id ?? '—'}`} />
        <details className="diff-group">
          <summary>Unchanged ({unchanged.length})</summary>
          <ul>{unchanged.map((a) => <AssignmentRow key={a.assignment_id} a={a} />)}</ul>
        </details>
        <p className="totals">
          Weighted ETA change {formatSeconds(Math.abs(diff.totals.weighted_eta_delta_s))}
          {diff.totals.weighted_eta_delta_s < 0 ? ' less' : ' more'} · units moved {diff.totals.units_moved} · added {diff.totals.units_added} ·
          released {diff.totals.units_released} · needs unmet {diff.totals.needs_unmet} · zones uncovered {diff.totals.zones_uncovered}
        </p>
      </div>

      <details className="assignments" open={view.kind !== 'proposed'}>
        <summary>All assignments ({plan.assignments.length})</summary>
        <ul>{plan.assignments.map((a) => <AssignmentRow key={a.assignment_id} a={a} />)}</ul>
      </details>
    </>
  )
}

export const PlanPanel = forwardRef<HTMLHeadingElement, PlanPanelProps>(function PlanPanel(
  { view, incidents, action, acked, commandsEnabled, onAck, onApprove, onOverride, onDismissNotice, approveRef },
  headerRef,
) {
  const plan = 'plan' in view ? view.plan : null
  const pending = action.kind === 'approving' || action.kind === 'busy_retrying'
  const needed = plan && view.kind === 'proposed' ? requiredAcks(plan) : []
  const missing = needed.filter((f) => !acked.includes(f))
  const blockers = plan ? unrecognisedValues(plan) : []
  const canApprove = view.kind === 'proposed' && commandsEnabled && !pending && missing.length === 0 && blockers.length === 0
  const blockedReason =
    view.kind === 'stale' ? 'plan is stale'
    : !commandsEnabled ? 'console is not live'
    : pending ? 'approval in progress'
    : blockers.length > 0 ? 'plan contains unrecognised values'
    : missing.length > 0 ? `${missing.length} flag${missing.length === 1 ? '' : 's'} need acknowledgement`
    : null
  const approveLabel = blockedReason ? `Approve and dispatch (simulated) — ${blockedReason}` : 'Approve and dispatch (simulated)'

  return (
    <section className={`plan plan-${view.kind}`} aria-labelledby="plan-title">
      <h2 id="plan-title" className="section-title" ref={headerRef} tabIndex={-1}>
        Plan
      </h2>
      <div className="plan-status-row">
        <span className="plan-status-icon" aria-hidden="true">{statusIcon(view)}</span>
        <p className="plan-status" role="status" aria-live="polite">
          {headerText(view, action)}
        </p>
      </div>
      {action.kind === 'rejected' && (
        <div className="notice notice-error" role="alert">
          {action.message} <span className="muted">({action.problem.code})</span>{' '}
          <button type="button" className="link" onClick={onDismissNotice}>Dismiss</button>
        </div>
      )}
      {blockers.length > 0 && (
        <p className="notice notice-error">Contains values this console cannot display ({blockers.join(', ')}); approval disabled.</p>
      )}
      {'approved' in view && view.approved && view.kind !== 'no_plan' && (
        <p className="muted">Approved plan v{view.approved.version} remains in force until a new plan is approved.</p>
      )}
      {plan && (
        <PlanBody plan={plan} view={view} incidents={incidents} acked={acked} onAck={onAck} onOverride={onOverride} editable={commandsEnabled && !pending && view.kind === 'proposed'} />
      )}
      <div className="plan-actions">
        {view.kind === 'proposed' && needed.length > 0 && (
          <div className="ack-progress" aria-hidden="true">
            <span>{needed.length - missing.length} of {needed.length} flags acknowledged</span>
            <span className="ack-bar"><span style={{ width: `${((needed.length - missing.length) / needed.length) * 100}%` }} /></span>
          </div>
        )}
        {view.kind === 'proposed' || view.kind === 'stale' ? (
          // aria-disabled (not disabled) keeps the button focusable so keyboard and screen
          // reader users reach it and hear why approval is blocked.
          <button
            ref={approveRef}
            type="button"
            className="primary"
            aria-disabled={!canApprove}
            aria-label={approveLabel}
            onClick={() => canApprove && onApprove()}
          >
            Approve &amp; dispatch (simulated)
          </button>
        ) : null}
        <button type="button" disabled={!commandsEnabled || pending || view.kind === 'computing' || view.kind === 'stale' || !plan} onClick={() => onOverride()}>
          Override…
        </button>
      </div>
      {!commandsEnabled && <p className="muted">Commands are disabled until the console is live.</p>}
    </section>
  )
})
