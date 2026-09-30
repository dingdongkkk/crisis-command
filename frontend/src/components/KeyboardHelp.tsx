import { Dialog } from './Dialog'

const KEYS: [string, string][] = [
  ['j / k', 'Next / previous incident'],
  ['Enter', 'Open triage for the focused incident'],
  ['a', 'Focus Approve (never approves by itself)'],
  ['o', 'Open the override dialog'],
  ['Esc', 'Close a dialog'],
]

export function KeyboardHelp({ onClose }: { onClose: () => void }) {
  return (
    <Dialog title="Keyboard shortcuts" onClose={onClose}>
      <dl className="keys">
        {KEYS.map(([k, v]) => (
          <div key={k}>
            <dt><kbd>{k}</kbd></dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      <div className="dialog-actions">
        <button type="button" className="primary" onClick={onClose}>Close</button>
      </div>
    </Dialog>
  )
}
