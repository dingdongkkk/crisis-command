import { act, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ConsoleApi } from '../api/types'
import { snapshotT10 } from '../mocks/mockApi'
import { ReportDialog } from './ReportDialog'

const browserWindow = window as unknown as Record<string, unknown>

class FakeSpeechRecognition {
  static instance: FakeSpeechRecognition | null = null
  continuous = false
  interimResults = false
  lang = ''
  maxAlternatives = 0
  onresult: ((event: never) => void) | null = null
  onerror: ((event: never) => void) | null = null
  onend: (() => void) | null = null
  start = vi.fn()
  stop = vi.fn(() => this.onend?.())
  abort = vi.fn()

  constructor() {
    FakeSpeechRecognition.instance = this
  }

  emit(transcript: string) {
    this.onresult?.({
      resultIndex: 0,
      results: [{ 0: { transcript }, length: 1, isFinal: true }],
    } as never)
  }
}

const reports = {
  submit: async () => { throw new Error('unused') },
  answer: async () => { throw new Error('unused') },
} as NonNullable<ConsoleApi['reports']>

afterEach(() => {
  delete browserWindow.SpeechRecognition
  delete browserWindow.webkitSpeechRecognition
  FakeSpeechRecognition.instance = null
})

describe('ReportDialog voice transcription', () => {
  it('keeps the browser transcript editable and requires explicit submission', async () => {
    browserWindow.webkitSpeechRecognition = FakeSpeechRecognition
    const user = userEvent.setup()
    render(<ReportDialog api={reports} snapshot={snapshotT10()} onClose={() => undefined} onCreated={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: 'Start voice transcription' }))
    const recognition = FakeSpeechRecognition.instance
    expect(recognition?.start).toHaveBeenCalledOnce()
    expect(recognition?.lang).toBe('en-IN')
    expect(screen.getByRole('status')).toHaveTextContent('Speak clearly')

    await act(() => recognition?.emit('there has been an accident near the school'))
    const transcript = screen.getByLabelText('Caller transcript')
    expect(transcript).toHaveValue('there has been an accident near the school')
    expect(transcript).toHaveAttribute('readonly')
    expect(screen.getByRole('button', { name: 'Record call' })).toBeDisabled()

    await user.click(screen.getByRole('button', { name: 'Stop voice transcription' }))
    expect(transcript).not.toHaveAttribute('readonly')
    expect(screen.getByRole('button', { name: 'Record call' })).toBeEnabled()
    await user.type(transcript, ' and two people are injured')
    expect(transcript).toHaveValue('there has been an accident near the school and two people are injured')
  })

  it('leaves text intake available when the browser has no speech API', () => {
    render(<ReportDialog api={reports} snapshot={snapshotT10()} onClose={() => undefined} onCreated={vi.fn()} />)
    expect(screen.getByRole('button', { name: 'Start voice transcription' })).toBeDisabled()
    expect(screen.getByText(/Voice is unavailable in this browser/)).toBeInTheDocument()
    expect(screen.getByLabelText('Caller transcript')).toBeEnabled()
  })
})

describe('pin on map', () => {
  const snapshot = snapshotT10()

  it('submits the pinned coordinates as an operator-entered location', async () => {
    const sent: unknown[] = []
    const api = {
      ...reports,
      submit: async (body: unknown) => {
        sent.push(body)
        return { ok: true as const, status: 201, replayed: false, body: { report_id: 'r', incident_id: 'i', sequence: 1, escalated: false } }
      },
    } as NonNullable<ConsoleApi['reports']>
    const user = userEvent.setup()
    render(<ReportDialog api={api} snapshot={snapshot} pinned={[77.6123, 12.9456]} onPickOnMap={() => undefined} onClose={() => undefined} onCreated={() => undefined} />)
    expect(screen.getByRole('option', { name: 'Pinned on map (12.9456°N, 77.6123°E)' })).toBeInTheDocument()
    await user.type(screen.getByLabelText('Caller transcript'), 'fire in the building')
    await user.click(screen.getByRole('button', { name: 'Record call' }))
    expect(sent[0]).toMatchObject({
      location: { type: 'Point', coordinates: [77.6123, 12.9456] },
      location_source: 'operator_entered',
    })
  })

  it('asks to pick on the map and keeps the draft while hidden', async () => {
    const pick = vi.fn()
    const user = userEvent.setup()
    const props = { api: reports, snapshot, onClose: () => undefined, onCreated: () => undefined, onPickOnMap: pick }
    const { rerender } = render(<ReportDialog {...props} />)
    await user.type(screen.getByLabelText('Caller transcript'), 'gas smell')
    await user.click(screen.getByRole('button', { name: 'Pin on map' }))
    expect(pick).toHaveBeenCalledOnce()
    rerender(<ReportDialog {...props} hidden />)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    rerender(<ReportDialog {...props} pinned={[77.6, 12.97]} />)
    expect(screen.getByLabelText('Caller transcript')).toHaveValue('gas smell')
    expect(screen.getByLabelText('Location')).toHaveValue('-1')
    expect(screen.getByRole('button', { name: 'Move pin' })).toBeInTheDocument()
  })
})
