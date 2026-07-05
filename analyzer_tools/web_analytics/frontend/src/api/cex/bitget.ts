import type { CexAdapter } from './types'
import { openVenueFeed, type VenueMsgResult } from './socket'

// 'books' channel — the backend's feed: full-depth snapshot + incremental
// updates with seq/pseq gap detection (gap → resync, mirroring
// ResyncRequired). size<=0 removes a level; top-20 emitted (emit_levels=20).
// Futures instType comes from the backend's Redis hash; the browser mirrors
// the md naming rule instead: USDC perps are named <BASE>PERP, everything
// else is USDT-FUTURES (the md's default_inst_type).

const EMIT_LEVELS = 20

export const bitget: CexAdapter = {
  supports: () => true,
  host: () => 'ws.bitget.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    const instType =
      opts.market === 'spot'
        ? 'SPOT'
        : sym.endsWith('PERP')
          ? 'USDC-FUTURES'
          : 'USDT-FUTURES'

    const bids = new Map<string, number>()
    const asks = new Map<string, number>()
    let synced = false
    let seq: number | null = null

    const apply = (side: Map<string, number>, levels: unknown, snapshot: boolean) => {
      if (snapshot) side.clear()
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

    const emit = (ts: number | null) => ({
      bids: [...bids.entries()]
        .map(([p, s]) => [Number(p), s])
        .sort((a, b) => b[0] - a[0])
        .slice(0, EMIT_LEVELS),
      asks: [...asks.entries()]
        .map(([p, s]) => [Number(p), s])
        .sort((a, b) => a[0] - b[0])
        .slice(0, EMIT_LEVELS),
      ts,
    })

    return openVenueFeed(
      {
        url: () => 'wss://ws.bitget.com/v2/ws/public',
        subscribeFrames: () => [
          JSON.stringify({
            op: 'subscribe',
            args: [{ instType, channel: 'books', instId: sym }],
          }),
        ],
        pingFrame: () => 'ping',
        reset: () => {
          bids.clear()
          asks.clear()
          synced = false
          seq = null
        },
        handle: (raw): VenueMsgResult => {
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
            code?: unknown
            action?: string
            arg?: { channel?: string }
            data?: unknown[]
          }
          if (m.event === 'error') {
            return { fatal: m.msg ?? String(m.code ?? 'subscribe error') }
          }
          if (m.event !== undefined) return null
          if (m.arg?.channel !== 'books' || !Array.isArray(m.data)) return null
          const d = m.data[0] as
            | { asks?: unknown; bids?: unknown; ts?: unknown; seq?: unknown; pseq?: unknown }
            | undefined
          if (!d) return null

          if (m.action === 'snapshot') {
            apply(bids, d.bids, true)
            apply(asks, d.asks, true)
            synced = true
            seq = d.seq != null ? Number(d.seq) : null
          } else if (m.action === 'update') {
            if (!synced) return null
            if (d.pseq != null && seq != null && Number(d.pseq) !== seq) {
              synced = false
              return 'resync' // sequence gap
            }
            apply(bids, d.bids, false)
            apply(asks, d.asks, false)
            seq = d.seq != null ? Number(d.seq) : seq
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
