import type { CexBook, CexFeedHandle, CexFeedOpts } from './types'

const PING_MS = 20_000
const BACKOFF_BASE_MS = 2_000
const BACKOFF_CAP_MS = 30_000

// What a venue's message handler can produce:
//   CexBook  — a renderable book
//   'resync' — local book state is broken (seq gap); recycle the socket
//   {fatal}  — unrecoverable (subscribe rejected); stop, no retry
//   null     — ignorable frame (acks, pongs, heartbeats)
export type VenueMsgResult = CexBook | 'resync' | { fatal: string } | null

export interface VenueSpec {
  // Function, not string: some venues need per-connect query params.
  url(): string
  subscribeFrames(): string[]
  // App-level keepalive payload; omit when the server drives keepalive.
  pingFrame?(): string
  handle(raw: string): VenueMsgResult
  // Clears per-connection state (delta-merge maps) before each connect.
  reset?(): void
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

    sock.onopen = () => {
      if (closed) return
      for (const frame of spec.subscribeFrames()) sock.send(frame)
      if (spec.pingFrame) {
        clearPing()
        pingId = window.setInterval(() => {
          if (sock.readyState === WebSocket.OPEN) sock.send(spec.pingFrame!())
        }, PING_MS)
      }
    }
    sock.onmessage = (ev) => {
      if (closed || typeof ev.data !== 'string') return
      const res = spec.handle(ev.data)
      if (res === null) return
      if (res === 'resync') {
        recycle()
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
