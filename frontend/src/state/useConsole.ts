import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react'
import type { ConnectionStatus, ConsoleApi } from '../api/types'
import type { OverrideCommand, Plan, Problem, StateSnapshot } from '../contracts'
import { derivePlanView, requiredAcks, type PlanView } from './planView'

export type PlanAction =
  | { kind: 'idle' }
  | { kind: 'approving' }
  | { kind: 'busy_retrying'; attempt: number }
  | { kind: 'rejected'; problem: Problem; message: string }

export interface ConsoleState {
  load: 'loading' | 'ready' | 'error'
  loadError: string | null
  snapshot: StateSnapshot | null
  connection: ConnectionStatus
  connectionDetail: string | null
  /** Wall-clock ms when the last live data arrived; drives the disconnected age. */
  lastLiveAt: number | null
  computing: boolean
  selectedIncidentId: string | null
  /** Acknowledgements bind to one plan version; a new plan starts empty. */
  acks: { planId: string | null; flagIds: string[] }
  planAction: PlanAction
  sessionChanged: boolean
}

type Action =
  | { type: 'loaded'; snapshot: StateSnapshot; now: number }
  | { type: 'load_failed'; message: string }
  | { type: 'state'; snapshot: StateSnapshot; now: number }
  | { type: 'connection'; status: ConnectionStatus; detail: string | null; now: number }
  | { type: 'computing'; computing: boolean }
  | { type: 'select'; incidentId: string | null }
  | { type: 'ack'; planId: string; flagId: string; checked: boolean }
  | { type: 'plan_action'; action: PlanAction }
  | { type: 'session_changed'; value: boolean }

export const initialConsoleState: ConsoleState = {
  load: 'loading',
  loadError: null,
  snapshot: null,
  connection: 'connecting',
  connectionDetail: null,
  lastLiveAt: null,
  computing: false,
  selectedIncidentId: null,
  acks: { planId: null, flagIds: [] },
  planAction: { kind: 'idle' },
  sessionChanged: false,
}

function withSnapshot(state: ConsoleState, snapshot: StateSnapshot): ConsoleState {
  const proposalId = snapshot.current_proposal?.plan_id ?? null
  const acks = state.acks.planId === proposalId ? state.acks : { planId: proposalId, flagIds: [] }
  // Keep the operator's selection across updates while the incident still exists.
  const stillThere = snapshot.incidents.some((i) => i.incident_id === state.selectedIncidentId)
  const sessionChanged = state.snapshot !== null && state.snapshot.session_id !== snapshot.session_id
  return {
    ...state,
    snapshot,
    acks,
    computing: snapshot.current_proposal ? false : state.computing,
    selectedIncidentId: stillThere ? state.selectedIncidentId : null,
    sessionChanged: state.sessionChanged || sessionChanged,
  }
}

export function consoleReducer(state: ConsoleState, action: Action): ConsoleState {
  switch (action.type) {
    case 'loaded':
      return { ...withSnapshot(state, action.snapshot), load: 'ready', lastLiveAt: action.now }
    case 'load_failed':
      return { ...state, load: 'error', loadError: action.message, connection: 'error' }
    case 'state':
      return { ...withSnapshot(state, action.snapshot), lastLiveAt: action.now }
    case 'connection':
      return {
        ...state,
        connection: action.status,
        connectionDetail: action.detail,
        lastLiveAt: action.status === 'live' || action.status === 'degraded' ? action.now : state.lastLiveAt,
      }
    case 'computing':
      return { ...state, computing: action.computing }
    case 'select':
      return { ...state, selectedIncidentId: action.incidentId }
    case 'ack': {
      if (state.acks.planId !== action.planId) return state
      const others = state.acks.flagIds.filter((f) => f !== action.flagId)
      return { ...state, acks: { planId: action.planId, flagIds: action.checked ? [...others, action.flagId] : others } }
    }
    case 'plan_action':
      return { ...state, planAction: action.action }
    case 'session_changed':
      return { ...state, sessionChanged: action.value }
  }
}

/** Commands require a live (or degraded-but-live) connection: otherwise the operator
 *  cannot know the current planning sequence (0006). */
export const commandsEnabled = (s: ConsoleState): boolean =>
  s.load === 'ready' && (s.connection === 'live' || s.connection === 'degraded')

const newKey = (): string => crypto.randomUUID()

export function useConsole(api: ConsoleApi) {
  const [state, dispatch] = useReducer(consoleReducer, initialConsoleState)
  const stateRef = useRef(state)
  useEffect(() => {
    stateRef.current = state
  }, [state])

  useEffect(() => {
    let cancelled = false
    api
      .loadState()
      .then((snapshot) => !cancelled && dispatch({ type: 'loaded', snapshot, now: Date.now() }))
      .catch((error: unknown) =>
        !cancelled &&
        dispatch({ type: 'load_failed', message: error instanceof Error ? error.message : String((error as Problem)?.title ?? error) }),
      )
    const disconnect = api.connect((update) => {
      if (cancelled) return
      if (update.kind === 'state') dispatch({ type: 'state', snapshot: update.state, now: Date.now() })
      else if (update.kind === 'connection')
        dispatch({ type: 'connection', status: update.status, detail: update.detail ?? null, now: Date.now() })
      else dispatch({ type: 'computing', computing: update.computing })
    })
    return () => {
      cancelled = true
      disconnect()
    }
  }, [api])

  const planView: PlanView | null = useMemo(
    () => (state.snapshot ? derivePlanView(state.snapshot, state.computing) : null),
    [state.snapshot, state.computing],
  )

  const approve = useCallback(
    async (plan: Plan, note?: string) => {
      const snapshot = stateRef.current.snapshot
      if (!snapshot) return
      const key = newKey() // one key per operator decision; reused for busy retries only
      const body = {
        expected_session_id: snapshot.session_id,
        expected_plan_version: plan.version,
        expected_planning_sequence: plan.based_on_planning_sequence,
        acknowledged_flag_ids: requiredAcks(plan).filter((f) => stateRef.current.acks.flagIds.includes(f)),
        ...(note ? { note } : {}),
      }
      dispatch({ type: 'plan_action', action: { kind: 'approving' } })
      for (let attempt = 1; attempt <= 3; attempt++) {
        const result = await api.approve(plan.plan_id, body, key)
        if (result.ok) {
          dispatch({ type: 'plan_action', action: { kind: 'idle' } })
          return
        }
        const { problem } = result
        if (problem.code === 'DATABASE_BUSY' && attempt < 3) {
          dispatch({ type: 'plan_action', action: { kind: 'busy_retrying', attempt } })
          await new Promise((r) => setTimeout(r, (result.retryAfterS ?? 1) * 1000))
          continue
        }
        if (problem.code === 'STALE_SESSION') dispatch({ type: 'session_changed', value: true })
        dispatch({ type: 'plan_action', action: { kind: 'rejected', problem, message: approvalMessage(problem) } })
        return
      }
    },
    [api],
  )

  const submitOverride = useCallback(
    async (command: Omit<OverrideCommand, 'expected_session_id' | 'expected_plan_id' | 'expected_planning_sequence'>) => {
      const snapshot = stateRef.current.snapshot
      const plan = snapshot?.current_proposal ?? snapshot?.approved_plan
      if (!snapshot || !plan) throw new Error('No plan to override')
      return api.submitOverride(
        {
          ...command,
          expected_session_id: snapshot.session_id,
          expected_plan_id: plan.plan_id,
          expected_planning_sequence: snapshot.planning_sequence,
        } as OverrideCommand,
        newKey(),
      )
    },
    [api],
  )

  return {
    state,
    planView,
    select: (incidentId: string | null) => dispatch({ type: 'select', incidentId }),
    ack: (planId: string, flagId: string, checked: boolean) => dispatch({ type: 'ack', planId, flagId, checked }),
    approve,
    submitOverride,
    clearPlanAction: () => dispatch({ type: 'plan_action', action: { kind: 'idle' } }),
    clearSessionChanged: () => dispatch({ type: 'session_changed', value: false }),
  }
}

export function approvalMessage(problem: Problem): string {
  const current = problem.current as { plan_version?: number } | null | undefined
  switch (problem.code) {
    case 'STALE_PLAN':
      return `Not approved: plan changed${current?.plan_version ? ` (now v${current.plan_version})` : ''}. Review the new plan.`
    case 'PLAN_NOT_PROPOSED':
      return 'Not approved: this plan is no longer awaiting approval.'
    case 'UNACKNOWLEDGED_FLAGS':
      return 'Not approved: some flags still need acknowledgement.'
    case 'STALE_SESSION':
      return 'Simulation was reset. Your action was not applied.'
    case 'DATABASE_BUSY':
      return 'Server busy — approval not recorded. Try again.'
    default:
      return `Not approved: ${problem.title}`
  }
}
