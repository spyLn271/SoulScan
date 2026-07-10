import { type FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import {
  buildSubscribe,
  buildUnsubscribe,
  EXCHANGES,
  MARKETS,
  parseOrderBook,
  U64_MAX,
  type Exchange,
  type Market,
  type OrderBookMsg,
} from '../api/ws'
import { CEX_ADAPTERS, type CexBook } from '../api/cex'
import { EndpointChip } from '../components/EndpointChip'
import { Ladder } from '../components/Ladder'
import {
  DOT_BY_STATUS,
  VenueCardBody,
  type VenueCardView,
} from '../components/VenueCardBody'
import { pinCard, type LiveVenueEntry } from '../pinnedCards'
import { fmtTs, hms } from '../format/time'
import { getAuth } from '../auth'
import { usePersistedState } from '../hooks'

type ConnState = 'disconnected' | 'connecting' | 'connected'

interface LogLine {
  id: number
  time: string
  kind: 'info' | 'sent' | 'recv' | 'error'
  text: string
}

interface Sub {
  exchange: Exchange
  symbol: string
  market: Market
  latency: string
}

const MAX_LOG = 80
// Frames land in refs and are flushed to state on this tick, so a fast
// stream never causes per-message re-renders.
const FLUSH_MS = 200

const subKey = (s: Pick<Sub, 'exchange' | 'symbol' | 'market'>) =>
  `${s.exchange}|${s.market}|${s.symbol}`

function validateLatency(raw: string): { value: bigint | null; error: string | null } {
  const t = raw.trim()
  if (t === '') return { value: null, error: null }
  if (!/^\d+$/.test(t)) return { value: null, error: 'must be a non-negative integer' }
  const v = BigInt(t)
  if (v > U64_MAX) return { value: null, error: 'exceeds u64 max' }
  return { value: v, error: null }
}

export function WsOrderBooks() {
  const [path, setPath] = usePersistedState('ss.ws.path', '/ws')
  const [conn, setConn] = useState<ConnState>('disconnected')

  const [exchange, setExchange] = usePersistedState<Exchange>('ss.ws.exchange', 'binance')
  const [market, setMarket] = usePersistedState<Market>('ss.ws.market', 'spot')
  const [symbol, setSymbol] = usePersistedState('ss.ws.symbol', 'BTCUSDT')
  const [latency, setLatency] = usePersistedState('ss.ws.latency', '100')

  const [subs, setSubs] = useState<Sub[]>([])
  const [log, setLog] = useState<LogLine[]>([])
  const [book, setBook] = useState<OrderBookMsg | null>(null)
  const [frameCount, setFrameCount] = useState(0)
  const [rate, setRate] = useState(0)

  const [directCards, setDirectCards] = useState<VenueCardView[]>([])
  const [nowMs, setNowMs] = useState(0)

  const wsRef = useRef<WebSocket | null>(null)
  const hadOpenRef = useRef(false)
  const latestRef = useRef<OrderBookMsg | null>(null)
  const lastFlushedRef = useRef<OrderBookMsg | null>(null)
  const framesRef = useRef(0)
  const flushedCountRef = useRef(0)
  const lastRateRef = useRef(0)
  const logIdRef = useRef(0)

  const directsRef = useRef<Map<string, LiveVenueEntry>>(new Map())
  const directsDirtyRef = useRef(false)

  const latencyCheck = useMemo(() => validateLatency(latency), [latency])
  const canSubscribe =
    conn === 'connected' && symbol.trim() !== '' && latencyCheck.value !== null

  function addLog(kind: LogLine['kind'], text: string) {
    setLog((prev) =>
      [{ id: ++logIdRef.current, time: hms(new Date()), kind, text }, ...prev].slice(
        0,
        MAX_LOG,
      ),
    )
  }

  function openDirect(sub: Sub) {
    const key = subKey(sub)
    const existing = directsRef.current.get(key)
    if (existing) {
      existing.feed?.close()
      directsRef.current.delete(key)
    }

    const adapter = CEX_ADAPTERS[sub.exchange]
    const supported = adapter !== undefined && adapter.supports(sub.market)
    const entry: LiveVenueEntry = {
      key,
      exchange: sub.exchange,
      symbol: sub.symbol,
      market: sub.market,
      host: supported ? adapter.host(sub.market) : null,
      status: supported ? 'connecting' : 'unsupported',
      feed: null,
      latest: null,
      lastFlushed: null,
      frames: 0,
      flushedCount: 0,
      rate: 0,
      lastAt: 0,
    }
    directsRef.current.set(key, entry)
    directsDirtyRef.current = true
    if (!supported) return

    // entry is per-feed: once it's deleted from the map, late events from a
    // dying socket mutate a detached object nobody reads
    entry.feed = adapter.open({
      symbol: sub.symbol,
      market: sub.market,
      onBook: (b) => {
        entry.latest = b
        entry.frames += 1
        entry.lastAt = Date.now()
      },
      onStatus: (status, detail) => {
        entry.status = status
        entry.detail = detail
        directsDirtyRef.current = true
      },
    })
  }

  function closeDirect(key: string) {
    const entry = directsRef.current.get(key)
    if (!entry) return
    entry.feed?.close()
    directsRef.current.delete(key)
    directsDirtyRef.current = true
  }

  function closeAllDirects() {
    for (const entry of directsRef.current.values()) entry.feed?.close()
    directsRef.current.clear()
    directsDirtyRef.current = true
  }

  // Hands the entry (and its open socket) to the floating layer, which
  // survives page unmount and tab switches.
  function pinDirect(key: string) {
    const entry = directsRef.current.get(key)
    if (!entry) return
    directsRef.current.delete(key)
    directsDirtyRef.current = true
    pinCard(entry)
  }

  // Flush tick + close sockets on unmount.
  useEffect(() => {
    const id = setInterval(() => {
      if (latestRef.current !== lastFlushedRef.current) {
        lastFlushedRef.current = latestRef.current
        setBook(latestRef.current)
      }
      const total = framesRef.current
      const delta = total - flushedCountRef.current
      flushedCountRef.current = total
      if (delta > 0 || lastRateRef.current > 0) {
        const r = Math.round(delta * (1000 / FLUSH_MS))
        lastRateRef.current = r
        setRate(r)
        setFrameCount(total)
      }

      let changed = directsDirtyRef.current
      directsDirtyRef.current = false
      for (const e of directsRef.current.values()) {
        if (e.latest !== e.lastFlushed) {
          e.lastFlushed = e.latest
          changed = true
        }
        const dDelta = e.frames - e.flushedCount
        e.flushedCount = e.frames
        if (dDelta > 0 || e.rate > 0) {
          e.rate = Math.round(dDelta * (1000 / FLUSH_MS))
          changed = true
        }
      }
      if (changed) {
        setDirectCards(
          [...directsRef.current.values()].map((e) => ({
            key: e.key,
            exchange: e.exchange,
            symbol: e.symbol,
            market: e.market,
            host: e.host,
            status: e.status,
            detail: e.detail,
            book: e.latest,
            frames: e.frames,
            rate: e.rate,
            lastAt: e.lastAt,
          })),
        )
      }
      // gated: with no direct feeds the page renders exactly as before
      if (directsRef.current.size > 0) setNowMs(Date.now())
    }, FLUSH_MS)
    return () => {
      clearInterval(id)
      wsRef.current?.close()
      for (const entry of directsRef.current.values()) entry.feed?.close()
      directsRef.current.clear()
    }
  }, [])

  function connect() {
    if (wsRef.current) return
    const p0 = path.trim() || '/ws'
    const p = p0.startsWith('/') ? p0 : `/${p0}`
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const base = `${proto}//${location.host}${p}`
    // Browsers can't set an Authorization header on a WebSocket; the JWT is
    // carried in the only header they allow — Sec-WebSocket-Protocol, offered
    // as ["bearer", <jwt>]. The backend must echo "bearer" (ws.protocols).
    const auth = getAuth()

    let ws: WebSocket
    try {
      ws = auth ? new WebSocket(base, ['bearer', auth.token]) : new WebSocket(base)
    } catch (err) {
      addLog('error', `invalid websocket url: ${String(err)}`)
      return
    }

    hadOpenRef.current = false
    wsRef.current = ws
    setConn('connecting')
    addLog('info', `connecting to ${base}${auth ? ' (token attached)' : ''}`)

    ws.onopen = () => {
      hadOpenRef.current = true
      setConn('connected')
      addLog('info', 'connected')
    }
    ws.onclose = (ev) => {
      wsRef.current = null
      setConn('disconnected')
      setSubs([]) // server-side subscription state died with the socket
      closeAllDirects()
      addLog('info', `closed (code ${ev.code}${ev.reason ? `, ${ev.reason}` : ''})`)
      if (ev.code === 1006 && !hadOpenRef.current) {
        addLog('error', 'closed before opening — no ws route at this path?')
      }
    }
    ws.onerror = () => addLog('error', 'websocket error')
    ws.onmessage = (ev) => {
      if (typeof ev.data !== 'string') {
        addLog('recv', 'non-text frame')
        return
      }
      const ob = parseOrderBook(ev.data)
      if (ob !== null) {
        // hot path: stash in refs, the flush tick renders it
        latestRef.current = ob
        framesRef.current += 1
      } else {
        // acks / server errors / anything that isn't an order book
        addLog('recv', ev.data.length > 400 ? `${ev.data.slice(0, 400)}…` : ev.data)
      }
    }
  }

  function disconnect() {
    wsRef.current?.close()
  }

  function sendSubscribe(e: FormEvent) {
    e.preventDefault()
    const ws = wsRef.current
    const lat = latencyCheck.value
    const sym = symbol.trim()
    if (!ws || ws.readyState !== WebSocket.OPEN || lat === null || sym === '') return

    const msg = buildSubscribe({ exchange, symbol: sym, market, latency: lat })
    ws.send(msg)
    addLog('sent', msg)
    const sub: Sub = { exchange, symbol: sym, market, latency: lat.toString() }
    setSubs((prev) => [...prev.filter((p) => subKey(p) !== subKey(sub)), sub])
    openDirect(sub)
  }

  function sendUnsubscribe(s: Sub) {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) return
    const msg = buildUnsubscribe(s)
    ws.send(msg)
    addLog('sent', msg)
    setSubs((prev) => prev.filter((p) => subKey(p) !== subKey(s)))
    closeDirect(subKey(s))
  }

  const soloCard = directCards.length === 1 ? directCards[0] : null

  return (
    <div className="tester">
      <div className="tester__col">
        <div className="panel">
          <div className="panel__head">
            <EndpointChip method="WS" path={path.trim() || '/ws'} />
            <span className={`dot dot--${conn}`} title={conn} />
          </div>
          <div className="conn-row">
            <label className="field">
              <span className="field__label">path</span>
              <input
                value={path}
                onChange={(e) => setPath(e.target.value)}
                disabled={conn !== 'disconnected'}
                placeholder="/ws"
                spellCheck={false}
              />
            </label>
            <button
              className="btn btn--inline"
              onClick={conn === 'disconnected' ? connect : disconnect}
            >
              {conn === 'disconnected'
                ? 'connect'
                : conn === 'connecting'
                  ? 'cancel'
                  : 'disconnect'}
            </button>
          </div>
        </div>

        <form className="panel" onSubmit={sendSubscribe}>
          <div className="panel__head">
            <h2>subscribe</h2>
          </div>

          <div className="form-row">
            <label className="field">
              <span className="field__label">exchange</span>
              <select
                value={exchange}
                onChange={(e) => setExchange(e.target.value as Exchange)}
              >
                {EXCHANGES.map((x) => (
                  <option key={x} value={x}>
                    {x}
                  </option>
                ))}
              </select>
            </label>
            <div className="field">
              <span className="field__label">market</span>
              <div className="seg">
                {MARKETS.map((m) => (
                  <button
                    type="button"
                    key={m}
                    className={`seg__btn ${market === m ? 'seg__btn--active' : ''}`}
                    onClick={() => setMarket(m)}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="form-row">
            <label className="field">
              <span className="field__label">symbol</span>
              <input
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="BTCUSDT"
                spellCheck={false}
              />
            </label>
            <label className="field">
              <span className="field__label">latency (ms)</span>
              <input
                value={latency}
                onChange={(e) => setLatency(e.target.value)}
                inputMode="numeric"
                spellCheck={false}
                className={latencyCheck.error ? 'input--error' : undefined}
              />
              {latencyCheck.error && (
                <span className="field__error">{latencyCheck.error}</span>
              )}
            </label>
          </div>

          <button className="btn" type="submit" disabled={!canSubscribe}>
            subscribe
          </button>
        </form>

        {subs.length > 0 && (
          <div className="panel">
            <div className="panel__head">
              <h2>subscriptions</h2>
              <span className="badge">{subs.length}</span>
            </div>
            {subs.map((s) => (
              <div key={subKey(s)} className="sub-row">
                <span>
                  {s.exchange} · {s.market} · {s.symbol}{' '}
                  <span className="sub-row__meta">@{s.latency}ms</span>
                </span>
                <button
                  className="btn btn--ghost btn--xs"
                  onClick={() => sendUnsubscribe(s)}
                >
                  unsubscribe
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="panel">
          <div className="panel__head">
            <h2>log</h2>
            <button className="btn btn--ghost btn--xs" onClick={() => setLog([])}>
              clear
            </button>
          </div>
          {log.length === 0 ? (
            <p className="empty">no events</p>
          ) : (
            <div className="log">
              {log.map((l) => (
                <div key={l.id} className={`log-line log-line--${l.kind}`}>
                  <span className="log-line__time">{l.time}</span>
                  {l.text}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="tester__col">
        <div className="panel">
          <div className="panel__head">
            <h2>order book</h2>
            {conn === 'connected' && rate > 0 && (
              <span className="badge badge--ok">live</span>
            )}
          </div>

          {book === null ? (
            <p className="empty">no frames</p>
          ) : (
            <>
              <div className="stats">
                <div className="stat">
                  <span className="stat__label">frames</span>
                  <span className="stat__value">
                    {frameCount.toLocaleString('en-US')}
                  </span>
                </div>
                <div className="stat">
                  <span className="stat__label">rate</span>
                  <span className="stat__value">{rate}/s</span>
                </div>
                <div className="stat">
                  <span className="stat__label">last frame</span>
                  <span className="stat__value">{fmtTs(book.timestamp_ms)}</span>
                </div>
                <div className="stat">
                  <span className="stat__label">levels</span>
                  <span className="stat__value">
                    {book.asks.length} × {book.bids.length}
                  </span>
                </div>
              </div>

              {subs.length > 1 && (
                <p className="empty note">
                  {subs.length} subscriptions on one socket — frames carry no id
                  and are unattributed
                </p>
              )}

              <Ladder book={book} />
            </>
          )}
        </div>

        {subs.length === 1 &&
          soloCard !== null &&
          soloCard.book !== null &&
          book !== null && (
            <DiffStrip
              backend={book}
              direct={soloCard.book}
              nowMs={nowMs}
              directLastAt={soloCard.lastAt}
            />
          )}

        {directCards.map((c) => (
          <div key={c.key} className="panel">
            <div className="panel__head">
              <h2>
                {c.exchange} · {c.market} · {c.symbol}
              </h2>
              <div className="panel__tools">
                {c.host !== null && <span className="meta">{c.host}</span>}
                {c.status !== 'unsupported' && (
                  <button
                    type="button"
                    className="btn btn--ghost btn--xs"
                    onClick={() => pinDirect(c.key)}
                  >
                    pin
                  </button>
                )}
                <span
                  className={`dot dot--${DOT_BY_STATUS[c.status]}`}
                  title={c.status}
                />
              </div>
            </div>
            <VenueCardBody view={c} />
          </div>
        ))}
      </div>
    </div>
  )
}

function DiffStrip({
  backend,
  direct,
  nowMs,
  directLastAt,
}: {
  backend: OrderBookMsg
  direct: CexBook
  nowMs: number
  directLastAt: number
}) {
  const bAsk = backend.asks[0]?.[0]
  const bBid = backend.bids[0]?.[0]
  const dAsk = direct.asks[0]?.[0]
  const dBid = direct.bids[0]?.[0]
  if (
    bAsk === undefined ||
    bBid === undefined ||
    dAsk === undefined ||
    dBid === undefined
  ) {
    return null
  }
  const bMid = (bAsk + bBid) / 2
  const dMid = (dAsk + dBid) / 2
  if (!(bMid > 0)) return null

  const bps = ((dMid - bMid) / bMid) * 1e4
  const backendAge = Math.max(0, nowMs - backend.timestamp_ms) / 1000
  const directAge = Math.max(0, nowMs - (direct.ts ?? directLastAt)) / 1000

  return (
    <div className="diff-strip">
      <span
        className={
          bps >= 0 ? 'diff-strip__delta--pos' : 'diff-strip__delta--neg'
        }
      >
        Δmid {bps >= 0 ? '+' : ''}
        {bps.toFixed(1)} bps
      </span>
      <span className="diff-strip__age">backend {backendAge.toFixed(1)}s</span>
      <span className="diff-strip__age">direct {directAge.toFixed(1)}s</span>
    </div>
  )
}
