import type { HistoryEntry } from '../hooks'

const pad2 = (n: number) => String(n).padStart(2, '0')

function timeOf(at: number): string {
  const d = new Date(at)
  return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`
}

interface Props<T> {
  entries: HistoryEntry<T>[]
  format: (data: T) => string
  // Restores form + stored response — never re-sends.
  onPick: (entry: HistoryEntry<T>) => void
  onClear: () => void
}

export function RequestHistory<T>({ entries, format, onPick, onClear }: Props<T>) {
  if (entries.length === 0) return null

  return (
    <div className="panel">
      <div className="panel__head">
        <h2>history</h2>
        <button type="button" className="btn btn--ghost btn--xs" onClick={onClear}>
          clear
        </button>
      </div>
      <div className="history">
        {entries.map((e, i) => (
          <button
            key={`${e.at}-${i}`}
            type="button"
            className="history-row"
            onClick={() => onPick(e)}
          >
            {e.result !== undefined && (
              <span
                className={`badge badge--sm ${e.result?.ok ? 'badge--ok' : 'badge--err'}`}
              >
                {e.result ? e.result.status : 'ERR'}
              </span>
            )}
            <span className="history-row__label">{format(e.data)}</span>
            <span className="history-row__time">{timeOf(e.at)}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
