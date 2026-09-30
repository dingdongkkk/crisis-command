#!/usr/bin/env node
/**
 * Reproducible console screenshots with real waiting (vector tiles load in a web worker,
 * which headless `--virtual-time-budget` stalls). Drives an installed Chrome over the
 * DevTools protocol using Node's built-in fetch/WebSocket; no browser download.
 *
 *   npm run build && npx vite preview --host 127.0.0.1 --port 4291 &
 *   node scripts/screenshot.mjs http://127.0.0.1:4291 ../docs/screenshots/cc-04
 */
import { spawn } from 'node:child_process'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'

const [base = 'http://127.0.0.1:4291', outDir = '../docs/screenshots/cc-04'] = process.argv.slice(2)
const CHROME = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = 9333

const SHOTS = [
  { name: 'desktop-demo', width: 1440, height: 900, query: '?mock=demo' },
  { name: 'desktop-selected', width: 1440, height: 900, query: '?mock=demo', select: 'inc_0006' },
  { name: 'desktop-disconnected', width: 1440, height: 900, query: '?mock=disconnected' },
  { name: 'desktop-light', width: 1440, height: 900, query: '?mock=demo', theme: 'light' },
  { name: 'narrow-demo', width: 390, height: 844, query: '?mock=demo', mobile: true },
]

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const chrome = spawn(CHROME, [
  '--headless=new',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cc-shot-'))}`,
  '--use-angle=metal',
  '--hide-scrollbars',
  'about:blank',
], { stdio: 'ignore' })

try {
  let target
  for (let i = 0; i < 50 && !target; i++) {
    await sleep(200)
    target = await fetch(`http://127.0.0.1:${PORT}/json/list`).then((r) => r.json()).then((t) => t.find((x) => x.type === 'page')).catch(() => undefined)
  }
  if (!target) throw new Error('Chrome DevTools endpoint did not start')

  const ws = new WebSocket(target.webSocketDebuggerUrl)
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j })
  let id = 0
  const pending = new Map()
  ws.onmessage = (m) => {
    const msg = JSON.parse(m.data)
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg)
      pending.delete(msg.id)
    }
  }
  const send = (method, params = {}) => new Promise((r) => {
    const n = ++id
    pending.set(n, r)
    ws.send(JSON.stringify({ id: n, method, params }))
  })
  const evaluate = (expression) => send('Runtime.evaluate', { expression, awaitPromise: true })

  await send('Page.enable')
  for (const shot of SHOTS) {
    await send('Emulation.setDeviceMetricsOverride', { width: shot.width, height: shot.height, deviceScaleFactor: 1, mobile: !!shot.mobile })
    await send('Page.navigate', { url: `${base}/${shot.query}` })
    await sleep(1500)
    await evaluate(`localStorage.setItem('crisis-command-theme', '${shot.theme ?? 'dark'}'); location.reload()`)
    await sleep(6000) // styles, vector tiles, fonts and the mock's live updates
    if (shot.select) {
      await evaluate(`document.querySelector('[data-incident-id="${shot.select}"]')?.click()`)
      await sleep(3500)
    }
    const { result } = await send('Page.captureScreenshot', { format: 'png' })
    const file = resolve(outDir, `${shot.name}.png`)
    writeFileSync(file, Buffer.from(result.data, 'base64'))
    console.log('wrote', file)
  }
  ws.close()
} finally {
  chrome.kill()
}
