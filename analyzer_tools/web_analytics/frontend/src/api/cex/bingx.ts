import type { CexAdapter } from './types'
import { crossed, openVenueFeed, parseLevels, sortLevels, type VenueMsgResult } from './socket'

// Gzip binary frames; per-symbol sub {"id","reqType":"sub","dataType":
// "BTC-USDT@depth20"}; full top-20 snapshot per push. Wire = dash before the
// 4-char quote. Keepalive is the md's oddity verbatim: the client proactively
// sends the literal text "Pong" every 5s (server "Ping"/"Pong" frames are
// swallowed). Sizes pass through unscaled on both markets — the backend does
// the same, so the comparison stays consistent. No event ts on this feed.

const DEPTH_LEVEL = 20

export const bingx: CexAdapter = {
  supports: () => true,
  host: (market) =>
    market === 'spot' ? 'open-api-ws.bingx.com' : 'open-api-swap.bingx.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    if (sym.length <= 4) {
      opts.onStatus('error', 'symbol mapping')
      return { close() {} }
    }
    const wire = `${sym.slice(0, -4)}-${sym.slice(-4)}`
    const url =
      opts.market === 'spot'
        ? 'wss://open-api-ws.bingx.com/market'
        : 'wss://open-api-swap.bingx.com/swap-market'

    return openVenueFeed(
      {
        url: () => url,
        subscribeFrames: () => [
          JSON.stringify({ id: '1', reqType: 'sub', dataType: `${wire}@depth${DEPTH_LEVEL}` }),
        ],
        pingFrame: () => 'Pong',
        pingIntervalMs: 5_000,
        binary: 'gzip',
        handle: (raw): VenueMsgResult => {
          const stripped = raw.replace(/^"|"$/g, '')
          if (stripped === 'Ping' || stripped === 'Pong') return null
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as {
            code?: number
            msg?: string
            dataType?: string
            data?: { bids?: unknown; asks?: unknown } | null
          }
          if (typeof m.code === 'number' && m.code !== 0) {
            return { fatal: m.msg || `code ${m.code}` }
          }
          if (!m.dataType?.includes('@depth') || !m.data) return null // sub ack
          const rawBids = parseLevels(m.data.bids)
          const rawAsks = parseLevels(m.data.asks)
          if (!rawBids || !rawAsks) return null
          // the wire order is not trusted — the backend re-sorts, so do we
          const bids = sortLevels(rawBids, 'bids', DEPTH_LEVEL)
          const asks = sortLevels(rawAsks, 'asks', DEPTH_LEVEL)
          if (crossed(bids, asks)) return null
          return { bids, asks, ts: null }
        },
      },
      opts,
    )
  },
}
