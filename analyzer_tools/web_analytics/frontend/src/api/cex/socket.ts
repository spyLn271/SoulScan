import type { CexBook, CexFeedHandle, CexFeedOpts } from './types'

const DEFAULT_PING_MS = 20_000
const BACKOFF_BASE_MS = 2_000
const BACKOFF_CAP_MS = 30_000

// What a venue's message handler can produce:
//   CexBook   — a renderable book
//   'resync'  — local book state is broken (seq/checksum); recycle the socket
//   {fatal}   — unrecoverable (subscribe rejected); stop, no retry
//   {reply}   — send this frame back (server-initiated pings, resubscribes)
//   null      — ignorable frame (acks, pongs, heartbeats)
export type VenueMsgResult =
  | CexBook
  | 'resync'
  | { fatal: string }
  | { reply: string }
  | null

export interface VenueSpec {
  // Function, not string: some venues need per-connect query params.
  url(): string
  subscribeFrames(): string[]
  // App-level keepalive payload; omit when the server drives keepalive.
  pingFrame?(): string
  pingIntervalMs?: number
  // Decode binary frames: 'gzip' (app-layer gzip) or 'auto' (try
  // deflate-raw / gzip / deflate, then plain utf-8) — mirrors the backend's
  // _text() tolerance.
  binary?: 'gzip' | 'auto'
  handle(raw: string): VenueMsgResult
  // Clears per-connection state (delta-merge maps) before each connect.
  reset?(): void
}

async function inflate(buf: ArrayBuffer, format: CompressionFormat): Promise<string> {
  const stream = new Blob([buf]).stream().pipeThrough(new DecompressionStream(format))
  return new Response(stream).text()
}

async function decodeBinary(buf: ArrayBuffer, mode: 'gzip' | 'auto'): Promise<string | null> {
  if (mode === 'gzip') {
    try {
      return await inflate(buf, 'gzip')
    } catch {
      // fall through to utf-8 (some venues mix plain control frames in)
    }
    try {
      return new TextDecoder().decode(buf)
    } catch {
      return null
    }
  }
  for (const format of ['deflate-raw', 'gzip', 'deflate'] as const) {
    try {
      return await inflate(buf, format)
    } catch {
      // try next
    }
  }
  try {
    return new TextDecoder().decode(buf)
  } catch {
    return null
  }
}

export function openVenueFeed(spec: VenueSpec, opts: CexFeedOpts): CexFeedHandle {
  let closed = false
  let live = false
  let attempt = 0
  let ws: WebSocket | null = null
  let pingId: number | undefined
  let retryId: number | undefined

  function clearPing() {
    window.clearInterval(pingId)
    pingId = undefined
  }

  function teardownSocket() {
    clearPing()
    if (ws) {
      ws.onopen = null
      ws.onmessage = null
      ws.onerror = null
      ws.onclose = null
      try {
        ws.close()
      } catch {
        // already closing
      }
      ws = null
    }
  }

  function scheduleRetry() {
    if (closed) return
    const delay = Math.min(BACKOFF_BASE_MS * 2 ** attempt, BACKOFF_CAP_MS)
    attempt += 1
    window.clearTimeout(retryId)
    retryId = window.setTimeout(connect, delay)
  }

  function recycle() {
    teardownSocket()
    live = false
    scheduleRetry()
  }

  function connect() {
    if (closed) return
    spec.reset?.()
    live = false
    opts.onStatus('connecting')

    let sock: WebSocket
    try {
      sock = new WebSocket(spec.url())
    } catch (err) {
      opts.onStatus('error', String(err))
      return
    }
    ws = sock
    sock.binaryType = 'arraybuffer'
    // ordered decode pipeline for binary frames
    let decodeChain: Promise<void> = Promise.resolve()

    function process(raw: string) {
      const res = spec.handle(raw)
      if (res === null) return
      if (res === 'resync') {
        recycle()
        return
      }
      if ('reply' in res) {
        if (sock.readyState === WebSocket.OPEN) sock.send(res.reply)
        return
      }
      if ('fatal' in res) {
        // never self-heals — stop without retry
        closed = true
        window.clearTimeout(retryId)
        teardownSocket()
        opts.onStatus('error', res.fatal)
        return
      }
      if (!live) {
        live = true
        attempt = 0
        opts.onStatus('live')
      }
      opts.onBook(res)
    }

    sock.onopen = () => {
      if (closed) return
      for (const frame of spec.subscribeFrames()) sock.send(frame)
      if (spec.pingFrame) {
        clearPing()
        pingId = window.setInterval(() => {
          if (sock.readyState === WebSocket.OPEN) sock.send(spec.pingFrame!())
        }, spec.pingIntervalMs ?? DEFAULT_PING_MS)
      }
    }
    sock.onmessage = (ev) => {
      if (closed) return
      if (typeof ev.data === 'string') {
        process(ev.data)
        return
      }
      if (!spec.binary || !(ev.data instanceof ArrayBuffer)) return
      const buf = ev.data
      decodeChain = decodeChain
        .then(async () => {
          const text = await decodeBinary(buf, spec.binary!)
          if (!closed && ws === sock && text !== null) process(text)
        })
        .catch(() => {})
    }
    sock.onerror = () => {
      // onclose follows with the code; avoid double-handling
    }
    sock.onclose = (ev) => {
      if (closed) return
      opts.onStatus('error', `closed ${ev.code}`)
      recycle()
    }
  }

  connect()

  return {
    close() {
      if (closed) return
      closed = true
      window.clearTimeout(retryId)
      teardownSocket()
      opts.onStatus('closed')
    },
  }
}

// [["price","qty",...],...] -> number[][], reading only indices 0/1.
// Tolerates numeric elements (htx sends raw JSON numbers).
export function parseLevels(v: unknown): number[][] | null {
  if (!Array.isArray(v)) return null
  const out: number[][] = []
  for (const lvl of v) {
    if (!Array.isArray(lvl)) return null
    const p = Number(lvl[0])
    const q = Number(lvl[1])
    if (!Number.isFinite(p) || !Number.isFinite(q)) return null
    out.push([p, q])
  }
  return out
}

// Sorted copy: bids descending, asks ascending, qty>0 only, top-n.
export function sortLevels(levels: number[][], side: 'bids' | 'asks', n: number): number[][] {
  const filtered = levels.filter((l) => l[1] > 0)
  filtered.sort(side === 'bids' ? (a, b) => b[0] - a[0] : (a, b) => a[0] - b[0])
  return filtered.slice(0, n)
}

export function crossed(bids: number[][], asks: number[][]): boolean {
  return bids.length === 0 || asks.length === 0 || bids[0][0] >= asks[0][0]
}
