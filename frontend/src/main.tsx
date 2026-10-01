import '@fontsource-variable/inter'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/ibm-plex-mono/600.css'
import './map/worker'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { LiveConsoleApi } from './api/liveApi'
import type { ConsoleApi } from './api/types'
import { MockConsoleApi, scenarioFromLocation } from './mocks/mockApi'
import './styles.css'
import './command-center.css'

const root = document.getElementById('root')
if (!root) throw new Error('Missing #root element')

// Live backend by default (CC-09). `?mock=<scenario>` keeps the contract-valid mock for
// demos without a backend and for screenshots: demo|stale|busy|loading|error|empty|
// disconnected|degraded|world_changing.
const params = new URLSearchParams(window.location.search)
const api: ConsoleApi = params.has('mock')
  ? new MockConsoleApi(scenarioFromLocation(window.location.search))
  : new LiveConsoleApi({ baseUrl: import.meta.env.VITE_API_BASE ?? '/api' })

createRoot(root).render(
  <StrictMode>
    <App api={api} mapTiles={params.get('tiles') !== 'off'} />
  </StrictMode>,
)
