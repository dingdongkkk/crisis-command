/**
 * Contract-valid mock backend for CC-04. Every payload comes from the CC-01 fixtures in
 * `docs/decisions/examples/` (validated in tests); the mock only sequences them.
 * It contains no allocation or policy logic: outcomes are canned server responses.
 */
import type { ApiResult, ConsoleApi, LiveUpdate, RouteCandidatesView } from '../api/types'
import type {
  ApprovalAccepted,
  ApproveCommand,
  OverrideCommand,
  OverrideRecorded,
  Plan,
  Problem,
  StateSnapshot,
  Unit,
} from '../contracts'
import apiExamples from '../../../docs/decisions/examples/api.examples.json'
import events from '../../../docs/decisions/examples/events.valid.json'
import recordedRoutes from './fixtures/route-candidates-t10.json'

export type MockScenario =
  | 'demo'
  | 'stale'
  | 'busy'
  | 'loading'
  | 'error'
  | 'empty'
  | 'disconnected'
  | 'degraded'
  | 'world_changing'

export const MOCK_SCENARIOS: MockScenario[] = [
  'demo', 'stale', 'busy', 'loading', 'error', 'empty', 'disconnected', 'degraded', 'world_changing',
]

interface ApiCase {
  name: string
  response: { status: number; body: unknown }
}

const clone = <T>(value: T): T => structuredClone(value)
const example = (name: string): unknown => {
  const found = (apiExamples as unknown as ApiCase[]).find((c) => c.name === name)
  if (!found) throw new Error(`missing API example ${name}`)
  return clone(found.response.body)
}

/** T+10 snapshot at sequence 60: proposal v7 awaiting approval, v6 approved and dispatched. */
export const snapshotT10 = (): StateSnapshot => example('state_snapshot') as StateSnapshot
export const problemExample = (name: string): Problem => example(name) as Problem

function renumber(plan: Plan, version: number, basedOn: number): Plan {
  const next = clone(plan)
  next.plan_id = `plan_${String(version).padStart(4, '0')}`
  next.version = version
  next.based_on_planning_sequence = basedOn
  next.flags = next.flags.map((f) => ({ ...f, flag_id: f.flag_id.replace(/^flag_\d+/, `flag_${String(version).padStart(4, '0')}`) }))
  return next
}

/** State after the approval of v7 and its three simulated deliveries (events 61–67). */
function dispatchedState(base: StateSnapshot): StateSnapshot {
  const next = clone(base)
  const plan = next.current_proposal
  if (!plan) return next
  next.approved_plan = { ...plan, state: 'dispatched_simulated' }
  next.current_proposal = null
  const unitsAfter = new Map<string, Unit>()
  for (const e of events as unknown as { event_type: string; payload: { unit_after?: Unit } }[]) {
    if (e.event_type === 'SimulatedDispatchSent' && e.payload.unit_after) unitsAfter.set(e.payload.unit_after.unit_id, e.payload.unit_after)
  }
  next.units = next.units.map((u) => unitsAfter.get(u.unit_id) ?? u)
  next.as_of_sequence = 67
  next.planning_sequence = 67
  next.sim_time_s = 605
  return next
}

type Listener = (update: LiveUpdate) => void

export class MockConsoleApi implements ConsoleApi {
  private listeners = new Set<Listener>()
  private state: StateSnapshot
  private busyAttempts = 0
  readonly requests: { kind: 'approve' | 'override'; key: string; body: unknown }[] = []

  constructor(
    readonly scenario: MockScenario = 'demo',
    private readonly delayMs = 150,
  ) {
    this.state = snapshotT10()
    if (scenario === 'empty') {
      this.state = { ...this.state, incidents: [], triage_facts: [], reports: [], approved_plan: null, current_proposal: null, outbox: [] }
    }
  }

  private emit(update: LiveUpdate): void {
    for (const l of this.listeners) l(update)
  }

  private later<T>(value: T, ms = this.delayMs): Promise<T> {
    return new Promise((resolve) => setTimeout(() => resolve(value), ms))
  }

  private setState(next: StateSnapshot): void {
    this.state = next
    this.emit({ kind: 'state', state: clone(next) })
  }

  loadState(): Promise<StateSnapshot> {
    if (this.scenario === 'loading') return new Promise(() => undefined)
    if (this.scenario === 'error') {
      return new Promise((_, reject) => setTimeout(() => reject(new Error('Snapshot unavailable (SNAPSHOT_REQUIRED)')), this.delayMs))
    }
    return this.later(clone(this.state))
  }

  connect(listener: Listener): () => void {
    this.listeners.add(listener)
    const timers: ReturnType<typeof setTimeout>[] = []
    const at = (ms: number, update: LiveUpdate) => timers.push(setTimeout(() => listener(update), ms))
    switch (this.scenario) {
      case 'loading':
        break
      case 'error':
        at(this.delayMs, { kind: 'connection', status: 'error', detail: 'Snapshot unavailable' })
        break
      case 'disconnected':
        at(this.delayMs, { kind: 'connection', status: 'live' })
        at(this.delayMs * 2, { kind: 'connection', status: 'disconnected', detail: 'No message for 30 s' })
        break
      case 'degraded':
        at(this.delayMs, { kind: 'connection', status: 'degraded', detail: 'Language model unavailable — rule intake active' })
        break
      case 'world_changing':
        at(this.delayMs, { kind: 'connection', status: 'world_changing', detail: 'Material events arriving; recomputing' })
        break
      default:
        at(this.delayMs, { kind: 'connection', status: 'live' })
    }
    return () => {
      this.listeners.delete(listener)
      timers.forEach(clearTimeout)
    }
  }

  async approve(planId: string, body: ApproveCommand, key: string): Promise<ApiResult<ApprovalAccepted>> {
    this.requests.push({ kind: 'approve', key, body })
    const plan = this.state.current_proposal
    if (this.scenario === 'busy' && this.busyAttempts++ === 0) {
      return this.later({ ok: false, status: 503, problem: { type: 'https://crisis-command.local/problems/database-busy', title: 'Database busy', status: 503, code: 'DATABASE_BUSY' }, retryAfterS: 0 })
    }
    if (!plan || plan.plan_id !== planId) return this.later({ ok: false, status: 409, problem: problemExample('approve_already_approved') })
    const missing = plan.flags.filter((f) => f.requires_ack && !body.acknowledged_flag_ids.includes(f.flag_id))
    if (missing.length) {
      return this.later({ ok: false, status: 409, problem: { ...problemExample('approve_missing_ack'), missing_flag_ids: missing.map((f) => f.flag_id) } })
    }
    if (this.scenario === 'stale') {
      // The world changed (seq 59–60) before this approval committed.
      const next = clone(this.state)
      next.current_proposal = renumber(plan, 8, 60)
      next.as_of_sequence = 60
      next.planning_sequence = 60
      await this.later(null)
      this.setState(next)
      return { ok: false, status: 409, problem: problemExample('approve_stale') }
    }
    const accepted = (await this.later(example('approve_valid'))) as ApprovalAccepted
    const approved = clone(this.state)
    approved.approved_plan = { ...plan, state: 'dispatching' }
    approved.current_proposal = null
    approved.as_of_sequence = 64
    approved.planning_sequence = 61
    const dispatched = dispatchedState(this.state)
    this.setState(approved)
    setTimeout(() => this.setState(dispatched), this.delayMs * 4)
    return { ok: true, status: 200, body: accepted, replayed: false }
  }

  getRouteCandidates(incidentId: string): Promise<RouteCandidatesView | null> {
    const found = recordedRouteCandidates().find((c) => c.incident_id === incidentId) ?? null
    return this.later(found, this.delayMs * 2)
  }

  async submitOverride(body: OverrideCommand, key: string): Promise<ApiResult<OverrideRecorded>> {
    this.requests.push({ kind: 'override', key, body })
    if (body.expected_planning_sequence !== this.state.planning_sequence) {
      return this.later({ ok: false, status: 409, problem: problemExample('approve_stale') })
    }
    const locked = this.state.units.find((u) => u.unit_id === body.unit_id && (u.status === 'on_scene' || u.status === 'transporting'))
    if (body.kind === 'pin' && locked) {
      const conflict = problemExample('override_pin_conflict')
      conflict.conflicts = [{ code: 'UNIT_LOCKED', unit_id: locked.unit_id, detail: `${locked.unit_id} is ${locked.status} at ${locked.current_task?.incident_id ?? 'its incident'}` }]
      return this.later({ ok: false, status: 409, problem: conflict })
    }
    const unit = this.state.units.find((u) => u.unit_id === body.unit_id)
    if (body.kind === 'pin' && unit?.type === 'bls' && body.need_id?.endsWith('_als')) {
      return this.later({ ok: false, status: 409, problem: problemExample('override_bls_to_als_pin_invalid') })
    }
    const recorded = (await this.later(example('override_bls_bridge_valid'))) as OverrideRecorded
    const proposal = this.state.current_proposal
    this.emit({ kind: 'computing', computing: true })
    const recomputed = clone(this.state)
    recomputed.current_proposal = null
    this.setState(recomputed)
    if (proposal) {
      setTimeout(() => {
        const next = clone(recomputed)
        const plan = renumber(proposal, proposal.version + 1, next.planning_sequence)
        plan.soft_consequences = [{ metric: 'weighted_eta_s', delta: 0, override_id: recorded.override_id }]
        next.current_proposal = plan
        this.emit({ kind: 'computing', computing: false })
        this.setState(next)
      }, this.delayMs * 3)
    }
    return { ok: true, status: 201, body: recorded, replayed: false }
  }
}

/** Real CC-07 router output recorded for the T+10 snapshot (seq 60). */
export const recordedRouteCandidates = (): RouteCandidatesView[] =>
  clone((recordedRoutes as unknown as { items: RouteCandidatesView[] }).items)

export function scenarioFromLocation(search: string): MockScenario {
  const value = new URLSearchParams(search).get('mock')
  return MOCK_SCENARIOS.includes(value as MockScenario) ? (value as MockScenario) : 'demo'
}
