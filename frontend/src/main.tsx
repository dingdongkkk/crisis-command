import '@fontsource-variable/inter'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/ibm-plex-mono/600.css'
import './map/worker'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { LiveConsoleApi } from './api/liveApi'
import type { ConsoleApi } from './api/types'
import { MockConsoleApi, scenarioFromLocation } from './mocks/mockApi'
import { ConsoleRoot } from './components/ConsoleRoot'
import './styles.css'
import './command-center.css'
import './map-layout.css'

const root = document.getElementById('root')
if (!root) throw new Error('Missing #root element')

// Live backend by default (CC-09). `?mock=<scenario>` keeps the contract-valid mock for
// demos without a backend and for screenshots: demo|stale|busy|loading|error|empty|
// disconnected|degraded|world_changing.
const params = new URLSearchParams(window.location.search)
// Hosted static build (e.g. Vercel): no backend exists, so the console runs on its built-in
// synthetic T+10 scenario and says so. The live API/WebSocket backend runs locally.
// A configured backend (VITE_API_BASE) always wins: the hosted console is then fully live.
const staticDemo = import.meta.env.VITE_DEMO_MODE === 'static' && !import.meta.env.VITE_API_BASE
const api: ConsoleApi =
  params.has('mock') || staticDemo
    ? new MockConsoleApi(scenarioFromLocation(window.location.search))
    : new LiveConsoleApi({ baseUrl: import.meta.env.VITE_API_BASE ?? '/api' })

createRoot(root).render(
  <StrictMode>
{staticDemo && (
      <p className="notice notice-strip static-demo-note" role="note">
        Hosted preview on built-in synthetic data (Bengaluru, T+10). The live backend, scenario
        controls and simulated calls run locally with <code>scripts/demo.sh</code>.
      </p>
    )}
    <ConsoleRoot api={api} mapTiles={params.get('tiles') !== 'off'} tourMode={params.get('tour')} />
  </StrictMode>,
)
