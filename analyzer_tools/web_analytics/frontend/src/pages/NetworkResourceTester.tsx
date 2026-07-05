import { type FormEvent, useState } from 'react'
import { apiGetRaw } from '../api/client'
import {
  fromStoredResult,
  runRequest,
  toStoredResult,
  type TestResult,
} from '../api/testClient'
import { ResponsePanel } from '../components/ResponsePanel'
import { CopyButton } from '../components/CopyButton'
import { EndpointChip } from '../components/EndpointChip'
import { RequestHistory } from '../components/RequestHistory'
import { usePersistedState, useRequestHistory } from '../hooks'

const NETWORKS = ['solana', 'ethereum', 'bnb', 'arb', 'base']

interface Props {
  // e.g. "/v1/tokens" -> GET /api/v1/tokens/{network}
  basePath: string
}

export function NetworkResourceTester({ basePath }: Props) {
  const [network, setNetwork] = usePersistedState(`ss.net.${basePath}`, 'solana')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TestResult | null>(null)
  const [sentUrl, setSentUrl] = useState<string | null>(null)

  const hist = useRequestHistory<{ network: string }>(`ss.hist${basePath}`)

  const trimmed = network.trim()
  const canSubmit = !pending && trimmed !== ''
  const routePath = `/api${basePath}/{network}`

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (trimmed === '') return

    const path = `${basePath}/${encodeURIComponent(trimmed)}`
    setSentUrl(`/api${path}`)
    setError(null)
    setResult(null)
    setPending(true)
    const { result: res, error: err } = await runRequest(() => apiGetRaw(path))
    setResult(res)
    setError(err)
    setPending(false)
    hist.push({ network: trimmed }, res ? toStoredResult(res) : null)
  }

  return (
    <div className="tester">
      <div className="tester__col">
        <form className="panel" onSubmit={onSubmit}>
          <div className="panel__head">
            <EndpointChip method="GET" path={routePath} />
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
            {pending ? 'fetching…' : 'fetch'}
          </button>
        </form>

        <RequestHistory
          entries={hist.entries}
          format={(d) => d.network}
          onClear={hist.clear}
          onPick={(e) => {
            setNetwork(e.data.network)
            setSentUrl(`/api${basePath}/${encodeURIComponent(e.data.network)}`)
            setResult(e.result ? fromStoredResult(e.result) : null)
            setError(null)
          }}
        />

        {sentUrl && (
          <div className="panel">
            <div className="panel__head">
              <h2>request</h2>
              <CopyButton text={sentUrl} />
            </div>
            <pre className="code-block">GET {sentUrl}</pre>
          </div>
        )}
      </div>

      <div className="tester__col">
        <ResponsePanel pending={pending} error={error} result={result} />
      </div>
    </div>
  )
}
