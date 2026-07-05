import type { Market } from '../ws'
import type { CexAdapter } from './types'
import { openVenueFeed, parseLevels, type VenueMsgResult } from './socket'

// Partial Book Depth: full top-20 snapshot every 100ms — the exact feed the
// backend's own connector consumes. Spot payload uses bids/asks and carries
// no event time; futures uses b/a and E (event ms). No client ping needed:
// the server sends WS-protocol pings that the browser answers automatically.

function handleFrame(raw: string, market: Market): VenueMsgResult {
  let msg: unknown
  try {
    msg = JSON.parse(raw)
  } catch {
    return null
  }
  if (typeof msg !== 'object' || msg === null) return null
  const data = (msg as { data?: unknown }).data
  // subscribe ack {result:null,id:1} has no data envelope
  if (typeof data !== 'object' || data === null) return null
  const d = data as Record<string, unknown>
  const bids = parseLevels(market === 'spot' ? d.bids : d.b)
  const asks = parseLevels(market === 'spot' ? d.asks : d.a)
  if (!bids || !asks) return null
  const ts = market === 'futures' && typeof d.E === 'number' ? d.E : null
  return { asks, bids, ts }
}

export const binance: CexAdapter = {
  supports: () => true,
  host: (market) => (market === 'spot' ? 'stream.binance.com' : 'fstream.binance.com'),
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    const url =
      opts.market === 'spot'
        ? 'wss://stream.binance.com:9443/stream'
        : 'wss://fstream.binance.com/stream'
    return openVenueFeed(
      {
        url: () => url,
        subscribeFrames: () => [
          JSON.stringify({
            method: 'SUBSCRIBE',
            params: [`${sym.toLowerCase()}@depth20@100ms`],
            id: 1,
          }),
        ],
        handle: (raw) => handleFrame(raw, opts.market),
      },
      opts,
    )
  },
}
