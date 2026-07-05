import { type FormEvent, useMemo, useState } from 'react'
import { apiPostRaw } from '../api/client'
import {
  serializeGetQuote,
  SOR_ENDPOINT,
  U128_MAX,
  type GetQuote,
} from '../api/sor'
import {
  fromStoredResult,
  runRequest,
  toStoredResult,
  type TestResult,
} from '../api/testClient'
import { ResponsePanel } from '../components/ResponsePanel'
import { JsonView } from '../components/JsonView'
import { CopyButton } from '../components/CopyButton'
import { EndpointChip } from '../components/EndpointChip'
import { RequestHistory } from '../components/RequestHistory'
import { usePersistedState, useRequestHistory } from '../hooks'

const NETWORKS = ['solana', 'ethereum', 'bnb', 'arb', 'base']

interface SorSnapshot {
  network: string
  address0: string
  address1: string
  amount: string
  aToB: boolean
  amountIsIn: boolean
}

function validateAmount(raw: string): { value: bigint | null; error: string | null } {
  const t = raw.trim()
  if (t === '') return { value: null, error: null }
  if (!/^\d+$/.test(t)) return { value: null, error: 'must be a non-negative integer' }
  const v = BigInt(t)
  if (v > U128_MAX) return { value: null, error: 'exceeds u128 max' }
  return { value: v, error: null }
}

export function SorTester() {
  const [network, setNetwork] = usePersistedState('ss.sor.network', 'solana')
  const [address0, setAddress0] = usePersistedState('ss.sor.address0', '')
  const [address1, setAddress1] = usePersistedState('ss.sor.address1', '')
  const [amount, setAmount] = usePersistedState('ss.sor.amount', '')
  const [aToB, setAToB] = usePersistedState('ss.sor.aToB', true)
  const [amountSpecifiedIsIn, setAmountSpecifiedIsIn] = usePersistedState(
    'ss.sor.amountIsIn',
    true,
  )

  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<TestResult | null>(null)
  const [sentBody, setSentBody] = useState<string | null>(null)

  const hist = useRequestHistory<SorSnapshot>('ss.hist.sor')
  const amountCheck = useMemo(() => validateAmount(amount), [amount])

  const canSubmit =
    !pending &&
    network.trim() !== '' &&
    address0.trim() !== '' &&
    address1.trim() !== '' &&
    amountCheck.value !== null

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (amountCheck.value === null) return

    const quote: GetQuote = {
      network: network.trim(),
      address0: address0.trim(),
      address1: address1.trim(),
      amount: amountCheck.value,
      a_to_b: aToB,
      amount_specified_is_in: amountSpecifiedIsIn,
    }
    const body = serializeGetQuote(quote)

    setSentBody(body)
    setError(null)
    setResult(null)
    setPending(true)
    const { result: res, error: err } = await runRequest(() =>
      apiPostRaw(SOR_ENDPOINT, body),
    )
    setResult(res)
    setError(err)
    setPending(false)
    hist.push(
      {
        network: quote.network,
        address0: quote.address0,
        address1: quote.address1,
        amount: amount.trim(),
        aToB,
        amountIsIn: amountSpecifiedIsIn,
      },
      res ? toStoredResult(res) : null,
    )
  }

  return (
    <div className="tester">
      <div className="tester__col">
        <form className="panel" onSubmit={onSubmit}>
          <div className="panel__head">
            <EndpointChip method="POST" path="/api/v1/sor" />
          </div>

          <label className="field">
            <span className="field__label">network</span>
            <input
              list="sor-networks"
              value={network}
              onChange={(e) => setNetwork(e.target.value)}
              placeholder="solana"
              spellCheck={false}
            />
            <datalist id="sor-networks">
              {NETWORKS.map((n) => (
                <option key={n} value={n} />
              ))}
            </datalist>
          </label>

          <label className="field">
            <span className="field__label">address0</span>
            <input
              value={address0}
              onChange={(e) => setAddress0(e.target.value)}
              placeholder="token in / pool token 0"
              spellCheck={false}
            />
          </label>

          <label className="field">
            <span className="field__label">address1</span>
            <input
              value={address1}
              onChange={(e) => setAddress1(e.target.value)}
              placeholder="token out / pool token 1"
              spellCheck={false}
            />
          </label>

          <label className="field">
            <span className="field__label">amount</span>
            <input
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="1000000000000000000"
              inputMode="numeric"
              spellCheck={false}
              className={amountCheck.error ? 'input--error' : undefined}
            />
            {amountCheck.error && (
              <span className="field__error">{amountCheck.error}</span>
            )}
          </label>

          <div className="toggles">
            <label className="toggle">
              <input
                type="checkbox"
                checked={aToB}
                onChange={(e) => setAToB(e.target.checked)}
              />
              <span>a_to_b</span>
            </label>
            <label className="toggle">
              <input
                type="checkbox"
                checked={amountSpecifiedIsIn}
                onChange={(e) => setAmountSpecifiedIsIn(e.target.checked)}
              />
              <span>amount_specified_is_in</span>
            </label>
          </div>

          <button className="btn" type="submit" disabled={!canSubmit}>
            {pending ? 'sending…' : 'send'}
          </button>
        </form>

        <RequestHistory
          entries={hist.entries}
          format={(d) => `${d.network} · ${d.amount}`}
          onClear={hist.clear}
          onPick={(e) => {
            const d = e.data
            setNetwork(d.network)
            setAddress0(d.address0)
            setAddress1(d.address1)
            setAmount(d.amount)
            setAToB(d.aToB)
            setAmountSpecifiedIsIn(d.amountIsIn)
            const v = validateAmount(d.amount).value
            setSentBody(
              v !== null
                ? serializeGetQuote({
                    network: d.network,
                    address0: d.address0,
                    address1: d.address1,
                    amount: v,
                    a_to_b: d.aToB,
                    amount_specified_is_in: d.amountIsIn,
                  })
                : null,
            )
            setResult(e.result ? fromStoredResult(e.result) : null)
            setError(null)
          }}
        />

        {sentBody && (
          <div className="panel">
            <div className="panel__head">
              <h2>request body</h2>
              <CopyButton text={sentBody} />
            </div>
            <JsonView text={sentBody} />
          </div>
        )}
      </div>

      <div className="tester__col">
        <ResponsePanel pending={pending} error={error} result={result} />
      </div>
    </div>
  )
}
