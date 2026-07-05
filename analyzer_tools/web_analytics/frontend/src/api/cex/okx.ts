import type { Market } from '../ws'
import type { CexAdapter } from './types'
import { crc32, crcMatches } from './crc32'
import { openVenueFeed, type VenueMsgResult } from './socket'

// 'books' channel — the same 400-depth snapshot+incremental feed the backend
// consumes, with the CRC32 checksum verified on updates (mismatch → resync,
// mirroring ResyncRequired). Book is kept as RAW wire strings because the
// checksum is computed pre-scaling; top-20 emitted (emit_levels=20). SWAP
// sizes are contracts scaled by ctVal — the backend reads ctVal from Redis,
// the browser fetches it from OKX's public REST (CORS-open, probe-verified).

const QUOTES = ['USDT', 'USDC']
const EMIT_LEVELS = 20
const CHECKSUM_DEPTH = 25

function instIdOf(symbol: string, market: Market): string | null {
  const quote = QUOTES.find((q) => symbol.endsWith(q) && symbol.length > q.length)
  if (!quote) return null
  const base = symbol.slice(0, -quote.length)
  return market === 'spot' ? `${base}-${quote}` : `${base}-${quote}-SWAP`
}

type RawSide = Map<string, string> // price -> size, wire strings

function applyRaw(side: RawSide, levels: unknown, snapshot: boolean) {
  if (snapshot) side.clear()
  if (!Array.isArray(levels)) return
  for (const lvl of levels) {
    if (!Array.isArray(lvl)) continue
    const price = String(lvl[0])
    const size = String(lvl[1])
    if (!snapshot && !(Number(size) > 0)) side.delete(price)
    else if (Number(size) > 0 || snapshot) side.set(price, size)
  }
}

function sortedRaw(side: RawSide, dir: 'desc' | 'asc'): [string, string][] {
  const entries = [...side.entries()]
  entries.sort(
    dir === 'desc'
      ? (a, b) => Number(b[0]) - Number(a[0])
      : (a, b) => Number(a[0]) - Number(b[0]),
  )
  return entries
}

// OKX checksum: top-25 bids(desc)/asks(asc) interleaved per level as
// 'bid_px:bid_sz:ask_px:ask_sz', remaining side appended when the other
// runs out, ':'-joined, CRC32.
function okxChecksum(bids: RawSide, asks: RawSide): number {
  const b = sortedRaw(bids, 'desc').slice(0, CHECKSUM_DEPTH)
  const a = sortedRaw(asks, 'asc').slice(0, CHECKSUM_DEPTH)
  const parts: string[] = []
  const n = Math.max(b.length, a.length)
  for (let i = 0; i < n; i++) {
    if (i < b.length) parts.push(b[i][0], b[i][1])
    if (i < a.length) parts.push(a[i][0], a[i][1])
  }
  return crc32(parts.join(':'))
}

export const okx: CexAdapter = {
  supports: () => true,
  host: () => 'ws.okx.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    const instId = instIdOf(sym, opts.market)
    if (instId === null) {
      opts.onStatus('error', 'symbol mapping')
      return { close() {} }
    }

    const bids: RawSide = new Map()
    const asks: RawSide = new Map()
    let synced = false
    let lastSeqId: number | null = null
    let mult = 1

    if (opts.market === 'futures') {
      fetch(`https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=${instId}`)
        .then((r) => r.json())
        .then((j: { data?: { ctVal?: string }[] }) => {
          const v = Number(j?.data?.[0]?.ctVal)
          if (Number.isFinite(v) && v > 0) mult = v
          else opts.onNote?.('sizes in contracts')
        })
        .catch(() => opts.onNote?.('sizes in contracts'))
    }

    const emit = (ts: number | null) => ({
      bids: sortedRaw(bids, 'desc')
        .slice(0, EMIT_LEVELS)
        .map(([p, s]) => [Number(p), Number(s) * mult]),
      asks: sortedRaw(asks, 'asc')
        .slice(0, EMIT_LEVELS)
        .map(([p, s]) => [Number(p), Number(s) * mult]),
      ts,
    })

    return openVenueFeed(
      {
        url: () => 'wss://ws.okx.com:8443/ws/v5/public',
        subscribeFrames: () => [
          JSON.stringify({ op: 'subscribe', args: [{ channel: 'books', instId }] }),
        ],
        pingFrame: () => 'ping',
        reset: () => {
          bids.clear()
          asks.clear()
          synced = false
          lastSeqId = null
        },
        handle: (raw): VenueMsgResult => {
          // plain-text pong is not JSON — check before parsing
          if (raw === 'pong') return null
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as {
            event?: string
            msg?: string
            code?: string
            action?: string
            arg?: { channel?: string }
            data?: unknown[]
          }
          if (m.event === 'error') return { fatal: m.msg ?? m.code ?? 'subscribe error' }
          if (m.event !== undefined) return null
          if (m.arg?.channel !== 'books' || !Array.isArray(m.data)) return null
          const d = m.data[0] as
            | {
                asks?: unknown
                bids?: unknown
                ts?: unknown
                checksum?: unknown
                seqId?: unknown
                prevSeqId?: unknown
              }
            | undefined
          if (!d) return null

          if (m.action === 'snapshot') {
            applyRaw(bids, d.bids, true)
            applyRaw(asks, d.asks, true)
            synced = true
            lastSeqId = d.seqId != null ? Number(d.seqId) : null
          } else if (m.action === 'update') {
            if (!synced) return null
            // integrity on the current wire is the seqId chain: each
            // update's prevSeqId links the previous frame's seqId
            if (
              d.prevSeqId != null &&
              lastSeqId != null &&
              Number(d.prevSeqId) !== lastSeqId
            ) {
              synced = false
              return 'resync'
            }
            applyRaw(bids, d.bids, false)
            applyRaw(asks, d.asks, false)
            lastSeqId = d.seqId != null ? Number(d.seqId) : lastSeqId
            // okx currently sends checksum:0 as a placeholder — verify only a
            // real value (the md's CRC scheme, kept for when it returns)
            if (typeof d.checksum === 'number' && d.checksum !== 0) {
              if (!crcMatches(okxChecksum(bids, asks), d.checksum)) {
                synced = false
                return 'resync'
              }
            }
          } else {
            return null
          }

          if (bids.size === 0 || asks.size === 0) return null
          const ts = Number(d.ts)
          return emit(Number.isFinite(ts) ? ts : null)
        },
      },
      opts,
    )
  },
}
