import type { CexAdapter } from './types'
import { crossed, openVenueFeed, parseLevels, sortLevels, type VenueMsgResult } from './socket'

// Spot only (the md marks futures disabled). Legacy old-wss gateway; frames
// are plain JSON or gzip (plus occasional non-JSON junk frames the backend
// also ignores — probe-verified). Wire = lowercase base_quote. Full top-50
// snapshots. No client ping — server sends {"action":"ping","ping":uuid} and
// expects the uuid echoed as {"action":"pong","pong":uuid}.

const QUOTES = ['USDT', 'USDC']
const DEPTH_LEVEL = 50

function wireOf(sym: string): string {
  const quote = QUOTES.find((q) => sym.endsWith(q) && sym.length > q.length)
  if (!quote) return sym.toLowerCase()
  return `${sym.slice(0, -quote.length).toLowerCase()}_${quote.toLowerCase()}`
}

export const lbank: CexAdapter = {
  supports: (market) => market === 'spot',
  host: () => 'www.lbank.com',
  open(opts) {
    const wire = wireOf(opts.symbol.trim().toUpperCase())

    return openVenueFeed(
      {
        url: () => 'wss://www.lbank.com/old-wss/ccws/ws/V3/',
        subscribeFrames: () => [
          JSON.stringify({
            action: 'subscribe',
            subscribe: 'depth',
            depth: 200,
            pair: wire,
            msgType: 2,
            limit: DEPTH_LEVEL,
            type: 0,
            dataType: 3,
            clientType: '',
          }),
        ],
        binary: 'auto',
        handle: (raw): VenueMsgResult => {
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null // junk/token frames on this gateway — ignored
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as {
            action?: string
            ping?: string
            pair?: string
            ds?: unknown
            cs?: unknown
            depth?: { bids?: unknown; asks?: unknown } | null
          }
          if (m.action === 'ping' && typeof m.ping === 'string') {
            return { reply: JSON.stringify({ action: 'pong', pong: m.ping }) }
          }
          if (!m.depth || typeof m.pair !== 'string') return null
          const rawBids = parseLevels(m.depth.bids)
          const rawAsks = parseLevels(m.depth.asks)
          if (!rawBids || !rawAsks) return null
          const bids = sortLevels(rawBids, 'bids', DEPTH_LEVEL)
          const asks = sortLevels(rawAsks, 'asks', DEPTH_LEVEL)
          if (crossed(bids, asks)) return null
          const ts = Number(m.ds ?? m.cs)
          return { bids, asks, ts: Number.isFinite(ts) ? ts : null }
        },
      },
      opts,
    )
  },
}
