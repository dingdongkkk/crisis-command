import type {
  AnswerCommand,
  ApprovalAccepted,
  ApproveCommand,
  DemoAdvanceResult,
  DemoResetResult,
  HealthResponse,
  ReportAccepted,
  ReportCommand,
  OverrideCommand,
  OverrideRecorded,
  Problem,
  RouteCandidates,
  StateSnapshot,
} from '../contracts'

/** `GET /routing/candidates` (CC-07): fastest road route from every unit to an incident. */
export type RouteCandidatesView = RouteCandidates
export type RouteCandidateView = RouteCandidates['candidates'][number]

/** Connection banner states from decision 0006. */
export type ConnectionStatus =
  | 'connecting'
  | 'live'
  | 'resyncing'
  | 'disconnected'
  | 'degraded'
  | 'world_changing'
  | 'error'

export type ApiResult<T> =
  | { ok: true; status: number; body: T; replayed: boolean }
  | { ok: false; status: number; problem: Problem; retryAfterS?: number }

export type LiveUpdate =
  | { kind: 'connection'; status: ConnectionStatus; detail?: string }
  | { kind: 'state'; state: StateSnapshot }
  | { kind: 'computing'; computing: boolean }

/**
 * The console's only dependency on the backend. CC-04 uses a contract-valid mock;
 * CC-09 implements this against HTTP + `/ws/events` without changing screens.
 */
export interface ConsoleApi {
  loadState(): Promise<StateSnapshot>
  approve(planId: string, body: ApproveCommand, idempotencyKey: string): Promise<ApiResult<ApprovalAccepted>>
  submitOverride(body: OverrideCommand, idempotencyKey: string): Promise<ApiResult<OverrideRecorded>>
  connect(listener: (update: LiveUpdate) => void): () => void
  /** Fastest road route from every unit to an incident (informational, not an allocation). */
  getRouteCandidates(incidentId: string): Promise<RouteCandidatesView | null>
  /** Simulation controls; present only when the backend runs in simulation mode. */
  simulation?: {
    advance(step: DemoStep, sessionId: string, key: string): Promise<ApiResult<DemoAdvanceResult>>
    reset(sessionId: string, key: string): Promise<ApiResult<DemoResetResult>>
  }
  /** Synthetic caller reports (text intake). */
  reports?: {
    submit(body: ReportCommand, key: string): Promise<ApiResult<ReportAccepted>>
    /** The caller's Yes / No / Not sure answer to the pending intake question. */
    answer(reportId: string, body: AnswerCommand, key: string): Promise<ApiResult<ReportAccepted>>
  }
  /** Providers and degraded causes (model/routing), polled alongside state. */
  health?(): Promise<ApiResult<HealthResponse>>
}

export type DemoStep = 'T+0' | 'T+2' | 'T+5' | 'T+10'
export const DEMO_STEPS: { step: DemoStep; simTimeS: number }[] = [
  { step: 'T+0', simTimeS: 0 },
  { step: 'T+2', simTimeS: 120 },
  { step: 'T+5', simTimeS: 300 },
  { step: 'T+10', simTimeS: 600 },
]
