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
