import { type FormEvent, useState } from 'react'
import { apiGetRaw } from '../api/client'
import { runRequest, type TestResult } from '../api/testClient'
import { ResponsePanel } from '../components/ResponsePanel'

// Networks seen in .env.example — just suggestions, the field is free-form.
const NETWORKS = ['solana', 'ethereum', 'bnb', 'arb', 'base']

interface Props {
  // Endpoint prefix; the network is appended as a path segment.
  // e.g. "/v1/tokens" -> GET /api/v1/tokens/{network}
  basePath: string
}

// Generic tester for `GET /api<basePath>/{network}` endpoints (metadata,
// tokens, …). One text field for the network, response as highlighted JSON.
export function NetworkResourceTester({ basePath }: Props) {
  const [network, setNetwork] = useState('solana')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TestResult | null>(null)
  const [sentUrl, setSentUrl] = useState<string | null>(null)

  const trimmed = network.trim()
  const canSubmit = !pending && trimmed !== ''
  const routePath = `/api${basePath}/{network}`

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (trimmed === '') return

    // network is a path segment, so encode it.
    const path = `${basePath}/${encodeURIComponent(trimmed)}`
    setSentUrl(`/api${path}`)
    setError(null)
    setResult(null)
    setPending(true)
    const { result: res, error: err } = await runRequest(() => apiGetRaw(path))
    setResult(res)
    setError(err)
    setPending(false)
  }

  return (
    <div className="tester">
      <div className="tester__col">
        <form className="panel" onSubmit={onSubmit}>
          <div className="panel__head">
            <code className="endpoint">GET {routePath}</code>
          </div>

          <label className="field">
            <span className="field__label">network</span>
            <input
              list="network-suggestions"
              value={network}
              onChange={(e) => setNetwork(e.target.value)}
              placeholder="solana"
              spellCheck={false}
            />
            <datalist id="network-suggestions">
              {NETWORKS.map((n) => (
                <option key={n} value={n} />
              ))}
            </datalist>
          </label>

          <button className="btn" type="submit" disabled={!canSubmit}>
            {pending ? 'Fetching…' : 'Send request'}
          </button>
        </form>

        {sentUrl && (
          <div className="panel">
            <div className="panel__head">
              <h2>Request</h2>
            </div>
            <pre className="code-block">GET {sentUrl}</pre>
          </div>
        )}
      </div>

      <div className="tester__col">
        <ResponsePanel
          pending={pending}
          error={error}
          result={result}
          hint={
            <>
              Is the axum backend running on <code>127.0.0.1:3000</code> with a{' '}
              <code>{routePath}</code> route?
            </>
          }
        />
      </div>
    </div>
  )
}
