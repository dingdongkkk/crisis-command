import { AudioLines, Mic, Square } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import type { ConsoleApi } from '../api/types'
import type { ReportAccepted, StateSnapshot } from '../contracts'
import { DEMO_PLACES } from '../state/scenario'
import { Dialog } from './Dialog'

interface ReportDialogProps {
  api: NonNullable<ConsoleApi['reports']>
  snapshot: StateSnapshot
  onClose: () => void
  onCreated: (result: ReportAccepted) => void
}

type SpeechLanguage = 'en-IN' | 'hi-IN'
type VoiceState =
  | { kind: 'idle' }
  | { kind: 'listening' }
  | { kind: 'stopping' }
  | { kind: 'error'; message: string }

interface SpeechResultEvent {
  resultIndex: number
  results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }>
}

interface SpeechErrorEvent {
  error: string
}

interface BrowserSpeechRecognition {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  onresult: ((event: SpeechResultEvent) => void) | null
  onerror: ((event: SpeechErrorEvent) => void) | null
  onend: (() => void) | null
  start: () => void
  stop: () => void
  abort: () => void
}

type SpeechRecognitionConstructor = new () => BrowserSpeechRecognition
type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor
  webkitSpeechRecognition?: SpeechRecognitionConstructor
}

function recognitionConstructor(): SpeechRecognitionConstructor | null {
  if (typeof window === 'undefined') return null
  const speechWindow = window as SpeechWindow
  return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null
}

const speechErrors: Record<string, string> = {
  'audio-capture': 'No working microphone was found.',
  'language-not-supported': 'That speech language is unavailable in this browser.',
  network: 'Speech recognition could not reach its service. Type the report instead.',
  'no-speech': 'No speech was detected. Try again or type the report.',
  'not-allowed': 'Microphone permission was denied. Allow access or type the report.',
  'service-not-allowed': 'Speech recognition is blocked by this browser.',
}

/** Simulated caller text → live intake (`POST /reports`). Synthetic data only. */
export function ReportDialog({ api, snapshot, onClose, onCreated }: ReportDialogProps) {
  const [text, setText] = useState('')
  const [place, setPlace] = useState(0)
  const [language, setLanguage] = useState<SpeechLanguage>('en-IN')
  const [voice, setVoice] = useState<VoiceState>({ kind: 'idle' })
  const [phase, setPhase] = useState<{ kind: 'editing' | 'submitting' } | { kind: 'error'; message: string }>({ kind: 'editing' })
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null)
  const transcriptBaseRef = useRef('')
  const speechSupported = recognitionConstructor() !== null

  useEffect(() => () => recognitionRef.current?.abort(), [])

  const stopVoice = (abort = false) => {
    const recognition = recognitionRef.current
    if (!recognition) return
    if (abort) recognition.abort()
    else {
      setVoice({ kind: 'stopping' })
      recognition.stop()
    }
  }

  const close = () => {
    stopVoice(true)
    onClose()
  }

  const startVoice = () => {
    const Recognition = recognitionConstructor()
    if (!Recognition) {
      setVoice({ kind: 'error', message: 'Voice transcription is unavailable here. Type the report instead.' })
      return
    }

    const recognition = new Recognition()
    recognition.lang = language
    recognition.continuous = true
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    transcriptBaseRef.current = text.trim()
    recognitionRef.current = recognition
    recognition.onresult = (event) => {
      const heard: string[] = []
      for (let index = 0; index < event.results.length; index += 1) {
        const transcript = event.results[index]?.[0]?.transcript.trim()
        if (transcript) heard.push(transcript)
      }
      setText([transcriptBaseRef.current, heard.join(' ')].filter(Boolean).join(' '))
    }
    recognition.onerror = (event) => {
      recognitionRef.current = null
      setVoice({ kind: 'error', message: speechErrors[event.error] ?? 'Voice transcription stopped unexpectedly. Type the report instead.' })
    }
    recognition.onend = () => {
      recognitionRef.current = null
      setVoice((current) => current.kind === 'error' ? current : { kind: 'idle' })
    }

    try {
      recognition.start()
      setVoice({ kind: 'listening' })
    } catch {
      recognitionRef.current = null
      setVoice({ kind: 'error', message: 'The microphone could not start. Type the report instead.' })
    }
  }

  const submit = async () => {
    setPhase({ kind: 'submitting' })
    const location = DEMO_PLACES[place] ?? DEMO_PLACES[0]
    if (!location) return
    const result = await api.submit(
      {
        expected_session_id: snapshot.session_id,
        channel: 'text_sim',
        text: text.trim(),
        location: { type: 'Point', coordinates: location.coordinates },
        location_source: 'caller_stated',
        sim_time_s: snapshot.sim_time_s,
      },
      crypto.randomUUID(),
    )
    if (result.ok) {
      onCreated(result.body)
      close()
    } else {
      setPhase({ kind: 'error', message: `${result.problem.title} (${result.problem.code})` })
    }
  }

  return (
    <Dialog title="Simulated call" onClose={close}>
      <p className="muted">Speak or type what a synthetic caller says. Review the transcript before recording it. Crisis Command stores no audio and contacts no real emergency service.</p>
      {phase.kind === 'error' && <p className="notice notice-error" role="alert">Report not recorded: {phase.message}</p>}
      <div className={`voice-intake voice-${voice.kind}`}>
        <div className="voice-heading">
          <span><AudioLines size={15} aria-hidden="true" /> Voice transcription <em>experimental</em></span>
          {voice.kind === 'listening' && <span className="voice-live"><i aria-hidden="true" /> Listening</span>}
          {voice.kind === 'stopping' && <span className="voice-live">Finishing…</span>}
        </div>
        <div className="voice-controls">
          <label>
            Spoken language
            <select value={language} disabled={voice.kind === 'listening' || voice.kind === 'stopping'} onChange={(event) => setLanguage(event.target.value as SpeechLanguage)}>
              <option value="en-IN">English / Hinglish</option>
              <option value="hi-IN">Hindi</option>
            </select>
          </label>
          <button
            type="button"
            className={voice.kind === 'listening' || voice.kind === 'stopping' ? 'voice-button voice-stop' : 'voice-button'}
            disabled={voice.kind === 'stopping' || !speechSupported}
            onClick={voice.kind === 'listening' ? () => stopVoice() : startVoice}
            aria-label={voice.kind === 'listening' ? 'Stop voice transcription' : 'Start voice transcription'}
          >
            {voice.kind === 'listening' || voice.kind === 'stopping' ? <Square size={14} aria-hidden="true" /> : <Mic size={15} aria-hidden="true" />}
            {voice.kind === 'listening' ? 'Stop' : voice.kind === 'stopping' ? 'Finishing…' : 'Start microphone'}
          </button>
        </div>
        {!speechSupported && <p className="voice-message">Voice is unavailable in this browser. The text intake remains fully functional.</p>}
        {voice.kind === 'error' && <p className="voice-message voice-error" role="alert">{voice.message}</p>}
        {(voice.kind === 'listening' || voice.kind === 'stopping') && <p className="voice-message" role="status">Speak clearly. Stop the microphone, correct the transcript, then record the call.</p>}
      </div>
      <label>
        Caller transcript
        <textarea value={text} readOnly={voice.kind === 'listening' || voice.kind === 'stopping'} maxLength={2000} onChange={(e) => setText(e.target.value)} placeholder="e.g. bhai accident ho gaya, do log ghayal hain, khoon beh raha hai" />
      </label>
      <label>
        Location
        <select value={place} onChange={(e) => setPlace(Number(e.target.value))}>
          {DEMO_PLACES.map((p, i) => (
            <option key={p.label} value={i}>{p.label}</option>
          ))}
        </select>
      </label>
      <div className="dialog-actions">
        <button type="button" onClick={close}>Cancel</button>
        <button type="button" className="primary" disabled={!text.trim() || phase.kind === 'submitting' || voice.kind === 'listening' || voice.kind === 'stopping'} onClick={() => void submit()}>
          {phase.kind === 'submitting' ? 'Recording…' : 'Record call'}
        </button>
      </div>
    </Dialog>
  )
}
