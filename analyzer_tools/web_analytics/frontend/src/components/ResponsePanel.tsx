import type { ReactNode } from 'react'
import type { TestResult } from '../api/testClient'
import { JsonView } from './JsonView'

interface Props {
  pending: boolean
  error: string | null
  result: TestResult | null
  // Optional extra guidance rendered under a network-level error.
  hint?: ReactNode
}

// Shared response viewer for every endpoint tester: status badge, latency,
// and the raw response body.
export function ResponsePanel({ pending, error, result, hint }: Props) {
  return (
    <div className="panel">
      <div className="panel__head">
        <h2>Response</h2>
        {result && (
          <span className={`badge ${result.ok ? 'badge--ok' : 'badge--err'}`}>
            {result.status} {result.statusText} · {result.durationMs}ms
          </span>
        )}
      </div>

      {!result && !error && !pending && (
        <p className="muted">Send a request to see the response.</p>
      )}
      {pending && <p className="muted">Waiting for backend…</p>}
      {error && (
        <div className="notice notice--err">
          <strong>Request failed.</strong> {error}
          {hint && <div className="muted small">{hint}</div>}
        </div>
      )}
      {result && <JsonView text={result.body} />}
    </div>
  )
}
