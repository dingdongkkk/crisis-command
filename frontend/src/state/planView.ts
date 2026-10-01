import type { Plan, StateSnapshot } from '../contracts'
import { isKnown } from './labels'

/** Plan panel states from decision 0006, derived only from server data plus `computing`. */
export type PlanView =
  | { kind: 'no_plan'; approved: Plan | null }
  | { kind: 'computing'; approved: Plan | null }
  | { kind: 'proposed'; plan: Plan; approved: Plan | null }
  | { kind: 'stale'; plan: Plan; approved: Plan | null }
  | { kind: 'approved' | 'dispatched' | 'partial_failed'; plan: Plan }
  | { kind: 'unrecognised'; plan: Plan; state: string }

const KNOWN_PLAN_STATES = new Set([
  'computing', 'proposed', 'superseded', 'approved', 'dispatching',
  'dispatched_simulated', 'dispatch_partial_failed', 'failed',
])

export function derivePlanView(snapshot: StateSnapshot, computing: boolean): PlanView {
  const proposal = snapshot.current_proposal
  const approved = snapshot.approved_plan
  if (proposal) {
    if (!KNOWN_PLAN_STATES.has(proposal.state)) return { kind: 'unrecognised', plan: proposal, state: proposal.state }
    // Approval requires the proposal to bind the current planning sequence (0005).
    if (proposal.based_on_planning_sequence !== snapshot.planning_sequence || proposal.state !== 'proposed') {
      return { kind: 'stale', plan: proposal, approved }
    }
    return { kind: 'proposed', plan: proposal, approved }
  }
  if (computing) return { kind: 'computing', approved }
  if (approved) {
    switch (approved.state) {
      case 'approved':
      case 'dispatching':
        return { kind: 'approved', plan: approved }
      case 'dispatched_simulated':
        return { kind: 'dispatched', plan: approved }
      case 'dispatch_partial_failed':
        return { kind: 'partial_failed', plan: approved }
      default:
        return KNOWN_PLAN_STATES.has(approved.state)
          ? { kind: 'no_plan', approved }
          : { kind: 'unrecognised', plan: approved, state: approved.state }
    }
  }
  return { kind: 'no_plan', approved: null }
}

/** Anything the UI cannot render faithfully blocks approval rather than being guessed. */
export function unrecognisedValues(plan: Plan): string[] {
  const bad: string[] = []
  for (const f of plan.flags) if (!isKnown('flagSeverity', f.severity)) bad.push(f.severity)
  for (const n of plan.unmet_needs) if (!isKnown('severity', n.severity)) bad.push(n.severity)
  for (const a of plan.assignments) if (a.role !== 'primary' && a.role !== 'bridge') bad.push(a.role)
  return bad
}

export function requiredAcks(plan: Plan): string[] {
  return plan.flags.filter((f) => f.requires_ack).map((f) => f.flag_id)
}
