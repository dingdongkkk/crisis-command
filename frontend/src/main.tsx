import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { App } from './App'
import { MockConsoleApi, scenarioFromLocation } from './mocks/mockApi'
import './styles.css'

const root = document.getElementById('root')
if (!root) throw new Error('Missing #root element')

// CC-04 runs against contract-valid mocks (?mock=demo|stale|busy|loading|error|empty|disconnected|degraded|world_changing).
// CC-09 replaces this with the live HTTP + WebSocket client.
const params = new URLSearchParams(window.location.search)
const api = new MockConsoleApi(scenarioFromLocation(window.location.search))

createRoot(root).render(
  <StrictMode>
    <App api={api} mapTiles={params.get('tiles') !== 'off'} />
  </StrictMode>,
)
