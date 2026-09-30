import type {
  ApprovalAccepted,
  ApproveCommand,
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
}
