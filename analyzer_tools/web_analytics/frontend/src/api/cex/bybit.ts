import type { CexAdapter } from './types'
import { openVenueFeed, parseLevels, type VenueMsgResult } from './socket'

// Spot: the legacy ws2 mergedDepth feed — the exact one the backend consumes
// (grouped snapshots, limit 40). The backend reads each symbol's dumpScale
// from its Redis metadata; the server rejects wrong values with
// {"code":"-100009","desc":"DumpScale error."} (probe-verified), so the
// browser auto-discovers it: subscribe at the finest scale and step down on
// rejection until accepted — landing on the instrument's own precision cap.
// Futures: the ws2 realtime_w feed requires Origin: https://www.bybit.com,
// which a browser cannot send — unsupported (no substitute feeds).

const SCALES = [8, 7, 6, 5, 4, 3, 2, 1, 0]

export const bybit: CexAdapter = {
  supports: (market) => market === 'spot',
  host: () => 'ws2.bybit.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()
    let scaleIdx = 0

    const subFrame = () =>
      JSON.stringify({
        topic: 'mergedDepth',
        event: 'sub',
        symbol: sym,
        limit: 40,
        params: { binary: false, dumpScale: SCALES[scaleIdx] },
      })

    return openVenueFeed(
      {
        url: () => `wss://ws2.bybit.com/spot/ws/quote/v2?_platform=2&tamp=${Date.now()}`,
        subscribeFrames: () => [subFrame()],
        pingFrame: () => JSON.stringify({ ping: Date.now() }),
        reset: () => {
          scaleIdx = 0
        },
        handle: (raw): VenueMsgResult => {
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as { topic?: string; desc?: string; code?: string; data?: unknown }
          if (typeof m.desc === 'string') {
            if (m.desc.includes('DumpScale')) {
              scaleIdx += 1
              if (scaleIdx >= SCALES.length) return { fatal: 'dumpScale rejected' }
              return { reply: subFrame() }
            }
            return { fatal: m.desc }
          }
          if (m.topic !== 'mergedDepth') return null // pongs / acks
          const d = Array.isArray(m.data) ? m.data[0] : m.data
          if (typeof d !== 'object' || d === null) return null
          const rec = d as { b?: unknown; a?: unknown; t?: unknown }
          const bids = parseLevels(rec.b)
          const asks = parseLevels(rec.a)
          if (!bids || !asks) return null
          const ts = Number(rec.t)
          return { asks, bids, ts: Number.isFinite(ts) ? ts : null }
        },
      },
      opts,
    )
  },
}
