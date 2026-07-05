import type { CexAdapter, CexBook } from './types'
import { openVenueFeed } from './socket'

// Official v5 public orderbook.50 for both markets (snapshot + deltas with a
// u-sequence). The backend's legacy ws2 feeds are unusable here: the futures
// one is Origin-locked, and the spot one accepts the socket but delivers no
// mergedDepth outside their environment (verified by live probe). Note the
// backend's bybit spot book is dumpScale-grouped, so small level differences
// vs this raw feed are expected.

export const bybit: CexAdapter = {
  supports: () => true,
  host: () => 'stream.bybit.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    const url =
      opts.market === 'spot'
        ? 'wss://stream.bybit.com/v5/public/spot'
        : 'wss://stream.bybit.com/v5/public/linear'

    // String price keys — exact deletes, no float-equality bugs.
    const bids = new Map<string, number>()
    const asks = new Map<string, number>()
    let lastU: number | null = null

    const apply = (side: Map<string, number>, levels: unknown) => {
      if (!Array.isArray(levels)) return
      for (const lvl of levels) {
        if (!Array.isArray(lvl)) continue
        const price = String(lvl[0])
        const size = Number(lvl[1])
        if (!Number.isFinite(size)) continue
        if (size <= 0) side.delete(price)
        else side.set(price, size)
      }
    }

    const fill = (side: Map<string, number>, levels: unknown) => {
      side.clear()
      apply(side, levels)
    }

    const emit = (ts: number | null): CexBook => ({
      asks: [...asks.entries()]
        .map(([p, s]) => [Number(p), s])
        .sort((x, y) => x[0] - y[0]),
      bids: [...bids.entries()]
        .map(([p, s]) => [Number(p), s])
        .sort((x, y) => y[0] - x[0]),
      ts,
    })

    return openVenueFeed(
      {
        url: () => url,
        subscribeFrames: () => [
          JSON.stringify({ op: 'subscribe', args: [`orderbook.50.${sym}`] }),
        ],
        pingFrame: () => JSON.stringify({ op: 'ping' }),
        reset: () => {
          bids.clear()
          asks.clear()
          lastU = null
        },
        handle: (raw) => {
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as {
            op?: string
            success?: boolean
            ret_msg?: string
            topic?: string
            type?: string
            ts?: number
            data?: { b?: unknown; a?: unknown; u?: unknown }
          }
          if (m.op === 'subscribe' && m.success === false) {
            return { fatal: m.ret_msg ?? 'subscribe rejected' }
          }
          if (m.op !== undefined) return null // pong / acks
          if (typeof m.topic !== 'string' || !m.topic.startsWith('orderbook.')) {
            return null
          }
          const d = m.data
          if (typeof d !== 'object' || d === null) return null
          const u = typeof d.u === 'number' ? d.u : null
          if (u === null) return null
          const ts = typeof m.ts === 'number' ? m.ts : null

          // u === 1 in a delta means the service restarted: treat as snapshot.
          if (m.type === 'snapshot' || u === 1) {
            fill(bids, d.b)
            fill(asks, d.a)
            lastU = u
            return emit(ts)
          }
          if (m.type !== 'delta') return null
          if (lastU === null) return null // delta before first snapshot
          if (u <= lastU) return null // stale/duplicate
          if (u !== lastU + 1) return 'resync' // sequence gap
          apply(bids, d.b)
          apply(asks, d.a)
          lastU = u
          return emit(ts)
        },
      },
      opts,
    )
  },
}
