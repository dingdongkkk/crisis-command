import type { HealthResponse } from './contracts'
import { CONTRACT_SCHEMA_VERSION } from './contracts'

export interface AppProps {
  /** Health payload when known; the live fetch arrives with CC-09. */
  health?: HealthResponse
}

/**
 * CC-02 shell only. Operator screens are CC-04. The banner states the product
 * boundary on every render so no screen can be mistaken for real dispatch.
 */
export function App({ health }: AppProps) {
  return (
    <>
      <div className="sim-banner" role="status">
        SIMULATION — synthetic data only. No real calls, dispatch or notifications.
      </div>
      <main>
        <h1>Crisis Command</h1>
        <p className="muted">
          Contract schema {CONTRACT_SCHEMA_VERSION}
          {health ? ` · backend ${health.status} · mode ${health.mode}` : ' · backend not connected'}
        </p>
      </main>
    </>
  )
}
