import type { CexAdapter } from './types'
import { crossed, openVenueFeed, parseLevels, sortLevels, type VenueMsgResult } from './socket'

// Spot only: the futures endpoint requires Origin: https://www.htx.com,
// which a browser cannot send. Gzip binary frames; per-symbol sub with the
// md's pick/symbol/step form; full top-50 snapshots. No client ping — the
// server sends {"ping": ts} and expects {"pong": ts} echoed back. Levels
// arrive as raw JSON numbers (probe-verified).

const DEPTH_LEVEL = 50

export const htx: CexAdapter = {
  supports: (market) => market === 'spot',
  host: () => 'www.htx.com',
  open(opts) {
    const wire = opts.symbol.trim().toLowerCase()

    return openVenueFeed(
      {
        url: () => 'wss://www.htx.com/-/s/pro/ws',
        subscribeFrames: () => [
          JSON.stringify({
            sub: `market.${wire}.depth.step0`,
            symbol: wire,
            pick: [`bids.${DEPTH_LEVEL}`, `asks.${DEPTH_LEVEL}`],
            step: 'step0',
          }),
        ],
        binary: 'gzip',
        handle: (raw): VenueMsgResult => {
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as {
            ping?: number
            ch?: string
            ts?: number
            status?: string
            'err-msg'?: string
            tick?: { bids?: unknown; asks?: unknown } | null
          }
          if (m.ping !== undefined) {
            return { reply: JSON.stringify({ pong: m.ping }) }
          }
          if (m.status === 'error') return { fatal: m['err-msg'] ?? 'subscribe error' }
          if (!m.ch?.endsWith('.depth.step0') || !m.tick) return null // acks
          const rawBids = parseLevels(m.tick.bids)
          const rawAsks = parseLevels(m.tick.asks)
          if (!rawBids || !rawAsks) return null
          const bids = sortLevels(rawBids, 'bids', DEPTH_LEVEL)
          const asks = sortLevels(rawAsks, 'asks', DEPTH_LEVEL)
          if (crossed(bids, asks)) return null
          return { bids, asks, ts: typeof m.ts === 'number' ? m.ts : null }
        },
      },
      opts,
    )
  },
}
