import type { CexAdapter } from './types'
import { openVenueFeed, parseLevels } from './socket'

// books15: full 15-level snapshot on every push (only the plain 'books'
// channel emits deltas). A hypothetical 'update' action is treated as a
// resync rather than rendering stale data.

export const bitget: CexAdapter = {
  supports: () => true,
  host: () => 'ws.bitget.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    const instType = opts.market === 'spot' ? 'SPOT' : 'USDT-FUTURES'
    return openVenueFeed(
      {
        url: () => 'wss://ws.bitget.com/v2/ws/public',
        subscribeFrames: () => [
          JSON.stringify({
            op: 'subscribe',
            args: [{ instType, channel: 'books15', instId: sym }],
          }),
        ],
        pingFrame: () => 'ping',
        handle: (raw) => {
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
          if (m.action === 'update') return 'resync'
          if (m.arg?.channel !== 'books15' || !Array.isArray(m.data)) return null
          const d = m.data[0] as
            | { asks?: unknown; bids?: unknown; ts?: unknown }
            | undefined
          if (!d) return null
          const asks = parseLevels(d.asks)
          const bids = parseLevels(d.bids)
          if (!asks || !bids) return null
          const ts = Number(d.ts)
          return { asks, bids, ts: Number.isFinite(ts) ? ts : null }
        },
      },
      opts,
    )
  },
}
