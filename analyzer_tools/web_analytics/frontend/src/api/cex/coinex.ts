import type { CexAdapter } from './types'
import { crc32, crcMatches } from './crc32'
import { openVenueFeed, type VenueMsgResult } from './socket'

// depth.subscribe_multi [[SYM, 50, "0"]] over permessage-deflate (the browser
// negotiates it natively). clean=true frames replace the book, clean=false
// are incremental (amount<=0 removes). CRC32 over the FULL book —
// 'price:amount' of bids desc then asks asc, ':'-joined — verified whenever
// the frame carries a checksum; mismatch → resync. Top-50 emitted
// (depth_level=50). Spot ws.coinex.com, futures perpetual.coinex.com.

const DEPTH_LEVEL = 50

export const coinex: CexAdapter = {
  supports: () => true,
  host: (market) => (market === 'spot' ? 'ws.coinex.com' : 'perpetual.coinex.com'),
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    const url =
      opts.market === 'spot' ? 'wss://ws.coinex.com/' : 'wss://perpetual.coinex.com/'

    // raw wire strings — the checksum is computed over them
    const bids = new Map<string, string>()
    const asks = new Map<string, string>()
    let synced = false

    const apply = (side: Map<string, string>, levels: unknown, snapshot: boolean) => {
      if (snapshot) side.clear()
      if (!Array.isArray(levels)) return
      for (const lvl of levels) {
        if (!Array.isArray(lvl)) continue
        const price = String(lvl[0])
        const amount = String(lvl[1])
        if (!snapshot && !(Number(amount) > 0)) side.delete(price)
        else if (Number(amount) > 0 || snapshot) side.set(price, amount)
      }
    }

    const sorted = (side: Map<string, string>, dir: 'desc' | 'asc') => {
      const entries = [...side.entries()]
      entries.sort(
        dir === 'desc'
          ? (a, b) => Number(b[0]) - Number(a[0])
          : (a, b) => Number(a[0]) - Number(b[0]),
      )
      return entries
    }

    const fullBookChecksum = () => {
      const parts: string[] = []
      for (const [p, a] of sorted(bids, 'desc')) parts.push(`${p}:${a}`)
      for (const [p, a] of sorted(asks, 'asc')) parts.push(`${p}:${a}`)
      return crc32(parts.join(':'))
    }

    const emit = (ts: number | null) => ({
      bids: sorted(bids, 'desc')
        .slice(0, DEPTH_LEVEL)
        .map(([p, a]) => [Number(p), Number(a)]),
      asks: sorted(asks, 'asc')
        .slice(0, DEPTH_LEVEL)
        .map(([p, a]) => [Number(p), Number(a)]),
      ts,
    })

    return openVenueFeed(
      {
        url: () => url,
        subscribeFrames: () => [
          JSON.stringify({
            id: 1,
            method: 'depth.subscribe_multi',
            params: [[sym, DEPTH_LEVEL, '0']],
          }),
        ],
        pingFrame: () => JSON.stringify({ id: 1, method: 'server.ping', params: [] }),
        pingIntervalMs: 10_000,
        reset: () => {
          bids.clear()
          asks.clear()
          synced = false
        },
        handle: (raw): VenueMsgResult => {
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as { method?: string; error?: unknown; params?: unknown[] }
          if (m.method !== 'depth.update') return null // acks / pongs
          if (!Array.isArray(m.params) || m.params.length < 3) return null
          const clean = m.params[0] === true
          const data = m.params[1] as
            | { bids?: unknown; asks?: unknown; checksum?: unknown; time?: unknown }
            | null
          if (typeof data !== 'object' || data === null) return null

          if (clean) {
            apply(bids, data.bids, true)
            apply(asks, data.asks, true)
            synced = true
          } else {
            if (!synced) return null
            apply(bids, data.bids, false)
            apply(asks, data.asks, false)
          }
          if (typeof data.checksum === 'number') {
            if (!crcMatches(fullBookChecksum(), data.checksum)) {
              synced = false
              return 'resync'
            }
          }

          const bidsSorted = sorted(bids, 'desc')
          const asksSorted = sorted(asks, 'asc')
          if (bidsSorted.length === 0 || asksSorted.length === 0) return null
          if (Number(bidsSorted[0][0]) >= Number(asksSorted[0][0])) return null // crossed
          const ts = Number(data.time)
          return emit(Number.isFinite(ts) ? ts : null)
        },
      },
      opts,
    )
  },
}
