import type { TestResult } from '../api/testClient'
import { JsonView } from './JsonView'
import { CopyButton } from './CopyButton'

interface Props {
  pending: boolean
  error: string | null
  result: TestResult | null
}

function fmtSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function ResponsePanel({ pending, error, result }: Props) {
  return (
    <div className="panel">
      <div className="panel__head">
        <h2>response</h2>
        {result && (
          <div className="panel__tools">
            <span className={`badge ${result.ok ? 'badge--ok' : 'badge--err'}`}>
              {result.status} {result.statusText}
            </span>
            <span className="meta">
              {result.durationMs} ms · {fmtSize(result.sizeBytes)}
            </span>
            <CopyButton text={result.body} />
          </div>
        )}
      </div>

      {!result && !error && !pending && <p className="empty">awaiting request</p>}
      {pending && (
        <div className="skeleton-group" aria-hidden="true">
          <div className="skeleton" style={{ width: '42%' }} />
          <div className="skeleton" style={{ width: '86%' }} />
          <div className="skeleton" style={{ width: '71%' }} />
          <div className="skeleton" style={{ width: '55%' }} />
        </div>
      )}
      {error && <div className="notice notice--err">request failed — {error}</div>}
      {result && <JsonView text={result.body} />}
    </div>
  )
}
