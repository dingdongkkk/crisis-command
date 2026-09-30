#!/usr/bin/env node
/**
 * Live end-to-end check (CC-09): drives the real console in headless Chrome over the
 * DevTools protocol against a running backend. Synthetic data and simulated dispatch only.
 *
 *   # backend: DATABASE_PATH=/tmp/e2e.db uv run uvicorn app.main:app --port 8291
 *   # console: CRISIS_BACKEND_URL=http://127.0.0.1:8291 npm run dev -- --port 5292
 *   node scripts/e2e-live.mjs http://127.0.0.1:5292 http://127.0.0.1:8291 ../docs/screenshots/cc-09
 *
 * Covers: live sync (page sequence catches the server), scenario advance, proposal shown as
 * not dispatched, approval dialog invalidated by a unit breakdown, a stale approval rejected by
 * the server, acknowledged approval → simulated dispatch, a simulated call, WebSocket loss
 * with backlog replay on reconnect, and a session reset resync. When the backend runs with
 * LLM_PROVIDER=gemini and GEMINI_ENDPOINT pointing at an unreachable local port, it also
 * drills model failure (no external request is made).
 */
import { spawn } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join, resolve } from 'node:path'
import { randomUUID } from 'node:crypto'

const [consoleUrl = 'http://127.0.0.1:5292', api = 'http://127.0.0.1:8291', shotDir] = process.argv.slice(2)
const CHROME = process.env.CHROME ?? '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const PORT = Number(process.env.CDP_PORT ?? 9334)
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// --- backend helpers -------------------------------------------------------------------
const state = () => fetch(`${api}/state`).then((r) => r.json())
async function post(path, body) {
  const r = await fetch(`${api}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Idempotency-Key': randomUUID() },
    body: JSON.stringify(body),
  })
  return { status: r.status, body: await r.json().catch(() => null) }
}

// --- CDP ---------------------------------------------------------------------------------
const chrome = spawn(CHROME, [
  '--headless=new',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), 'cc-e2e-'))}`,
  '--use-angle=metal',
  '--hide-scrollbars',
  'about:blank',
], { stdio: 'ignore' })

let send
async function attach() {
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
  send = (method, params = {}) => new Promise((r) => {
    const n = ++id
    pending.set(n, r)
    ws.send(JSON.stringify({ id: n, method, params }))
  })
  return ws
}

async function page(expression) {
  const { result } = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })
  if (result?.exceptionDetails) throw new Error(result.exceptionDetails.text)
  return result?.result?.value
}

async function waitFor(label, fn, timeoutMs = 20_000) {
  const start = Date.now()
  let last
  while (Date.now() - start < timeoutMs) {
    last = await fn().catch((e) => e)
    if (last === true || (last && last !== false && !(last instanceof Error))) return last
    await sleep(250)
  }
  throw new Error(`timed out waiting for: ${label}${last instanceof Error ? ` (${last.message})` : ''}`)
}

const text = () => page('document.body.innerText')
const pageSequence = async () => Number((await text()).match(/(?:Live · |as of )seq (\d+)/)?.[1] ?? NaN)
const clickButton = (label) => page(`(() => {
  const b = [...document.querySelectorAll('button')].find((e) => (e.getAttribute('aria-label') ?? e.textContent).trim().startsWith(${JSON.stringify(label)}))
  if (!b) return false
  b.click(); return true
})()`)
const clickInDialog = (label) => page(`(() => {
  const d = document.querySelector('[role=dialog]')
  const b = d && [...d.querySelectorAll('button')].find((e) => e.textContent.trim().startsWith(${JSON.stringify(label)}))
  if (!b) return false
  b.click(); return true
})()`)
const ackAll = () => page(`(() => { let n = 0; for (const b of document.querySelectorAll('input[id^="ack-"]')) if (!b.checked && !b.disabled) { b.click(); n++ } return n })()`)

async function shot(name) {
  if (!shotDir) return
  mkdirSync(resolve(shotDir), { recursive: true })
  await sleep(2500) // vector tiles load in a worker
  const { result } = await send('Page.captureScreenshot', { format: 'png' })
  writeFileSync(resolve(shotDir, `${name}.png`), Buffer.from(result.data, 'base64'))
}

/** The page is in sync when its displayed sequence equals the server's head. */
async function synced(label) {
  return waitFor(`${label}: console sequence reaches server head`, async () => {
    const s = await state()
    return (await pageSequence()) === s.as_of_sequence && s
  })
}

// --- checks --------------------------------------------------------------------------------
const results = []
async function check(name, fn) {
  const t0 = Date.now()
  try {
    const detail = await fn()
    results.push({ name, ok: true, ms: Date.now() - t0, detail })
    console.log(`PASS  ${name}${detail ? ` — ${detail}` : ''}`)
  } catch (error) {
    results.push({ name, ok: false, ms: Date.now() - t0, detail: error.message })
    console.log(`FAIL  ${name} — ${error.message}`)
    await shot(`fail-${results.length}`).catch(() => undefined)
    throw error
  }
}

const clock = (s) => `T+${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`

try {
  await attach()
  await send('Page.enable')
  await send('Network.enable')
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false })

  let session
  await check('reset to a fresh seeded session (API)', async () => {
    const before = await state()
    const r = await post('/demo/reset', { expected_session_id: before.session_id, fixture: 'demo-bengaluru-v1', seed: 7 })
    if (r.status !== 200) throw new Error(`reset ${r.status} ${JSON.stringify(r.body)}`)
    session = (await state()).session_id
    return `${before.session_id} → ${session}`
  })

  await check('console loads and goes live on the new session', async () => {
    await send('Page.navigate', { url: `${consoleUrl}/` })
    await waitFor('Live badge', async () => /Live · seq \d+/.test(await text()))
    await synced('initial load')
    if (!(await text()).includes(session)) throw new Error(`session ${session} not shown`)
    return (await text()).match(/Live · seq \d+[^\n]*/)?.[0]
  })

  for (const [step, simS] of [['T+0', 0], ['T+2', 120], ['T+5', 300], ['T+10', 600]]) {
    await check(`advance to ${step} from the console`, async () => {
      const before = (await state()).as_of_sequence
      await waitFor(`"Advance to ${step}" button`, () => clickButton(`Advance to ${step}`))
      // T+0 keeps the clock at 0, so wait for the step's events rather than the clock alone.
      await waitFor(`server at ${step}`, async () => {
        const st = await state()
        return st.sim_time_s === simS && st.as_of_sequence > before
      })
      const s = await synced(step)
      await waitFor(`badge shows ${clock(simS)}`, async () => (await text()).includes(`sim ${clock(simS)}`))
      return `seq ${s.as_of_sequence}, ${s.incidents.length} incidents`
    })
  }

  let proposal
  await check('proposal is shown as PROPOSED, not dispatched, and approval is gated', async () => {
    proposal = await waitFor('server proposal', async () => (await state()).current_proposal)
    await waitFor('PROPOSED header', async () => (await text()).includes(`PROPOSED v${proposal.version} — not dispatched`))
    const t = await text()
    if (/DISPATCHED \(simulated\)/.test(t)) throw new Error('unapproved plan presented as dispatched')
    const gated = await page(`[...document.querySelectorAll('button')].find((b) => (b.getAttribute('aria-label') ?? b.textContent).startsWith('Approve and dispatch'))?.getAttribute('aria-disabled')`)
    const needs = proposal.flags.filter((f) => f.requires_ack).length
    if (needs > 0 && gated !== 'true') throw new Error(`approve not gated with ${needs} unacknowledged flags`)
    await shot('01-proposed-t10')
    return `v${proposal.version}, ${proposal.assignments.length} assignments, ${needs} flags need acknowledgement`
  })

  let broken
  await check('a unit breakdown while the approval dialog is open voids the confirmation', async () => {
    await ackAll()
    if (!(await clickButton('Approve and dispatch (simulated)'))) throw new Error('approve button not found')
    await waitFor('approve dialog', async () => (await text()).includes(`Approve plan v${proposal.version}?`))
    broken = proposal.assignments[0].unit_id
    const r = await post(`/units/${broken}/status`, { expected_session_id: session, to_status: 'broken_down', sim_time_s: 600 })
    if (r.status !== 200) throw new Error(`breakdown ${r.status} ${JSON.stringify(r.body)}`)
    await waitFor('plan-changed dialog', async () => (await text()).includes('Plan changed — nothing approved'))
    const t = await text()
    if (t.includes(`Approve plan v${proposal.version}?`)) throw new Error('stale confirmation still offered')
    await shot('02-plan-changed-dialog')
    await clickInDialog('Review current plan')
    const s = await state()
    if (s.approved_plan) throw new Error('something was approved')
    return `${broken} broken down; confirmation for v${proposal.version} withdrawn`
  })

  let current
  await check('replanning excludes the broken unit and the console shows the new version', async () => {
    current = await waitFor('new proposal', async () => {
      const p = (await state()).current_proposal
      return p && p.version > proposal.version && p
    }, 30_000)
    if (current.assignments.some((a) => a.unit_id === broken)) throw new Error(`${broken} still assigned`)
    await waitFor('new PROPOSED header', async () => (await text()).includes(`PROPOSED v${current.version} — not dispatched`))
    await synced('after breakdown')
    return `v${proposal.version} → v${current.version}`
  })

  await check('the server rejects a stale approval of the superseded plan', async () => {
    const r = await post(`/plans/${proposal.plan_id}/approve`, {
      expected_session_id: session,
      expected_plan_version: proposal.version,
      expected_planning_sequence: proposal.based_on_planning_sequence,
      acknowledged_flag_ids: proposal.flags.filter((f) => f.requires_ack).map((f) => f.flag_id),
    })
    if (r.status < 400) throw new Error(`stale approval accepted (${r.status})`)
    if ((await state()).approved_plan) throw new Error('stale plan became approved')
    return `${r.status} ${r.body?.code}`
  })

  await check('acknowledged approval → simulated dispatch', async () => {
    const acked = await ackAll()
    if (!(await clickButton('Approve and dispatch (simulated)'))) throw new Error('approve button not found')
    await waitFor('approve dialog', async () => (await text()).includes(`Approve plan v${current.version}?`))
    await clickInDialog('Approve & dispatch (simulated)')
    await waitFor('dispatched header', async () => /(APPROVED|DISPATCHED \(simulated\)) v\d+/.test(await text()), 30_000)
    const s = await state()
    if (!s.approved_plan || s.approved_plan.version !== current.version) throw new Error('server has no matching approved plan')
    await waitFor('DISPATCHED (simulated)', async () => (await text()).includes(`DISPATCHED (simulated) v${current.version}`), 30_000)
    await synced('after dispatch')
    await shot('03-dispatched')
    return `${acked} flags acknowledged; v${current.version} dispatched (simulated), outbox ${s.outbox.length}`
  })

  await check('a simulated call creates a triaged incident', async () => {
    const before = (await state()).incidents.length
    if (!(await clickButton('Simulated call'))) throw new Error('Simulated call button not found')
    await waitFor('report dialog', async () => page(`!!document.querySelector('[role=dialog] textarea')`))
    await page(`(() => {
      const ta = document.querySelector('[role=dialog] textarea')
      Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, 'bhai accident ho gaya, do log ghayal hain, khoon beh raha hai')
      ta.dispatchEvent(new Event('input', { bubbles: true }))
      const sel = document.querySelector('[role=dialog] select')
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value').set.call(sel, '1')
      sel.dispatchEvent(new Event('change', { bubbles: true }))
    })()`)
    await clickInDialog('Record call')
    const s = await waitFor('new incident', async () => {
      const st = await state()
      return st.incidents.length > before && st
    })
    const created = s.incidents.at(-1)
    await synced('after report')
    await waitFor('incident in queue', async () => (await text()).includes(created.incident_id))
    await shot('04-simulated-call')
    return `${created.incident_id} ${created.kind} (${created.severity})`
  })

  await check('the caller answers the pending intake question from the triage panel', async () => {
    const s0 = await state()
    const pendingOf = (st) => {
      for (const f of st.triage_facts) {
        const last = f.questions_asked.at(-1)
        const inc = st.incidents.find((i) => i.incident_id === f.incident_id && i.status === 'active')
        if (inc && last && last.answer == null && !f.escalation.escalated) return { incident: inc, key: last.fact_key }
      }
      return null
    }
    let pending = pendingOf(s0)
    if (!pending) {
      // A vague call leaves critical facts unknown, so the intake asks one targeted question.
      await post('/reports', { expected_session_id: session, channel: 'text_sim', text: 'someone fell down near the bus stop', location: { type: 'Point', coordinates: [77.6408, 12.9784] }, location_source: 'caller_stated', sim_time_s: s0.sim_time_s })
      pending = await waitFor('a pending question', async () => pendingOf(await state()))
    }
    await synced('before answering')
    await page(`document.querySelector('[data-incident-id="${pending.incident.incident_id}"]')?.click()`)
    await waitFor('question group', async () => page(`!!document.querySelector('.pending-question')`))
    await page(`[...document.querySelectorAll('.pending-question button')].find((b) => b.textContent === 'No').click()`)
    const fact = await waitFor('answer recorded', async () => {
      const st = await state()
      const f = st.triage_facts.find((t) => t.incident_id === pending.incident.incident_id)?.facts.find((x) => x.key === pending.key)
      return f && f.source === 'caller_structured' && f
    })
    await synced('after answer')
    await shot('04b-intake-question-answered')
    return `${pending.incident.incident_id}: ${pending.key} = ${fact.value} (caller_structured)`
  })

  const health = await fetch(`${api}/health`).then((r) => r.json())
  if (health.llm_provider === 'gemini') {
    await check('model failure degrades visibly to rules-only intake (drill)', async () => {
      const s0 = await state()
      const r = await post('/reports', { expected_session_id: session, channel: 'text_sim', text: 'aag lagi hai, bahut dhuan hai', location: { type: 'Point', coordinates: [77.6101, 12.9352] }, location_source: 'caller_stated', sim_time_s: s0.sim_time_s })
      if (r.status !== 201) throw new Error(`report ${r.status} ${JSON.stringify(r.body)}`)
      const st = await state()
      const facts = st.triage_facts.find((t) => t.incident_id === r.body.incident_id)
      const fire = facts.facts.find((f) => f.key === 'fire_or_smoke')
      if (fire.value !== 'yes' || fire.source !== 'rule_adapter') throw new Error(`rules did not extract fire: ${JSON.stringify(fire)}`)
      const h = await fetch(`${api}/health`).then((x) => x.json())
      if (!h.degraded.includes('MODEL_UNAVAILABLE')) throw new Error('health not degraded')
      await waitFor('degraded notice', async () => (await text()).includes('Model adapter unavailable'))
      await shot('06-model-degraded')
      return `${r.body.incident_id} triaged by rules; health degraded ${JSON.stringify(h.degraded)}`
    })
  }

  await check('WebSocket loss shows Disconnected; reconnect replays the missed backlog', async () => {
    await send('Network.emulateNetworkConditions', { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 })
    await waitFor('Disconnected badge', async () => (await text()).includes('Disconnected'), 45_000)
    const frozen = await pageSequence().catch(() => NaN)
    await shot('05-disconnected')
    // world changes while the console is offline
    const s0 = await state()
    const idle = s0.units.find((u) => u.status === 'available')
    await post(`/units/${idle.unit_id}/status`, { expected_session_id: session, to_status: 'off_duty', sim_time_s: 600 })
    await send('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 })
    await waitFor('Live again', async () => /Live · seq \d+/.test(await text()), 30_000)
    const s = await synced('after reconnect')
    return `offline at seq ${Number.isNaN(frozen) ? '?' : frozen}; ${idle.unit_id} off duty while offline; caught up to seq ${s.as_of_sequence}`
  })

  await check('session reset from the console resyncs to the new session', async () => {
    await clickButton('Reset simulation')
    await waitFor('reset dialog', async () => (await text()).includes('Reset the simulation?'))
    await clickInDialog('Reset')
    const s = await waitFor('new session', async () => {
      const st = await state()
      return st.session_id !== session && st
    })
    await synced('after reset')
    await waitFor('new session shown', async () => (await text()).includes(s.session_id))
    if ((await text()).includes('DISPATCHED (simulated)')) throw new Error('old session plan still shown')
    return `${session} → ${s.session_id}`
  })
} catch {
  process.exitCode = 1
} finally {
  chrome.kill()
  const passed = results.filter((r) => r.ok).length
  console.log(`\n${passed}/${results.length} checks passed`)
  if (shotDir) {
    mkdirSync(resolve(shotDir), { recursive: true })
    writeFileSync(resolve(shotDir, 'e2e-results.json'), `${JSON.stringify({ consoleUrl, api, results }, null, 2)}\n`)
  }
}
