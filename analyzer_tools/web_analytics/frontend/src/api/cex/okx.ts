import type { Market } from '../ws'
import type { CexAdapter } from './types'
import { openVenueFeed, parseLevels } from './socket'

// books5: full 5-level snapshot per push (no checksum bookkeeping, unlike the
// 400-depth 'books' channel). Levels are [price, size, "0", orderCount]
// strings. NOTE: SWAP sizes are in contracts — ctVal lives in the backend's
// Redis and is unreachable from the browser, so the card labels them as-is.

const QUOTES = ['USDT', 'USDC']

function instIdOf(symbol: string, market: Market): string | null {
  const quote = QUOTES.find((q) => symbol.endsWith(q) && symbol.length > q.length)
  if (!quote) return null
  const base = symbol.slice(0, -quote.length)
  return market === 'spot' ? `${base}-${quote}` : `${base}-${quote}-SWAP`
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
    return openVenueFeed(
      {
        url: () => 'wss://ws.okx.com:8443/ws/v5/public',
        subscribeFrames: () => [
          JSON.stringify({ op: 'subscribe', args: [{ channel: 'books5', instId }] }),
        ],
        pingFrame: () => 'ping',
        handle: (raw) => {
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
            arg?: { channel?: string }
            data?: unknown[]
          }
          if (m.event === 'error') return { fatal: m.msg ?? m.code ?? 'subscribe error' }
          if (m.event !== undefined) return null
          if (m.arg?.channel !== 'books5' || !Array.isArray(m.data)) return null
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
