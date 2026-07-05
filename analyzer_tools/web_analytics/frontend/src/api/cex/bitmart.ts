import type { CexAdapter } from './types'
import { openVenueFeed, type VenueMsgResult } from './socket'

// Futures only. The spot host (ws-manager-compress.bitmart.com) refuses
// connections outside the backend's environment (probe-verified), so spot is
// unsupported. Futures v2 delivers ONE-SIDED frames (way=1 bids / way=2
// asks, depths as {price, vol} objects); a book is emitted only once both
// sides are cached — exactly the backend's assembly. Sizes are contracts
// scaled by contract_size; the backend reads it from Redis, the browser
// fetches it from BitMart's public REST (CORS *, probe-verified).

const DEPTH_LEVEL = 20

export const bitmart: CexAdapter = {
  supports: (market) => market === 'futures',
  host: () => 'openapi-ws-v2.bitmart.com',
  open(opts) {
    const sym = opts.symbol.trim().toUpperCase()

    let mult = 1
    fetch(`https://api-cloud-v2.bitmart.com/contract/public/details?symbol=${sym}`)
      .then((r) => r.json())
      .then((j: { data?: { symbols?: { contract_size?: string }[] } }) => {
        const v = Number(j?.data?.symbols?.[0]?.contract_size)
        if (Number.isFinite(v) && v > 0) mult = v
        else opts.onNote?.('sizes in contracts')
      })
      .catch(() => opts.onNote?.('sizes in contracts'))

    let bids: number[][] | null = null
    let asks: number[][] | null = null

    const parseSide = (depths: unknown): number[][] | null => {
      if (!Array.isArray(depths)) return null
      const out: number[][] = []
      for (const lvl of depths) {
        if (typeof lvl !== 'object' || lvl === null) return null
        const price = Number((lvl as { price?: unknown }).price)
        const vol = Number((lvl as { vol?: unknown }).vol)
        if (!Number.isFinite(price) || !Number.isFinite(vol)) return null
        if (vol > 0) out.push([price, vol])
      }
      return out
    }

    return openVenueFeed(
      {
        url: () => 'wss://openapi-ws-v2.bitmart.com/api?protocol=1.1',
        subscribeFrames: () => [
          JSON.stringify({ action: 'subscribe', args: [`futures/depth${DEPTH_LEVEL}:${sym}`] }),
        ],
        pingFrame: () => JSON.stringify({ action: 'ping' }),
        pingIntervalMs: 10_000,
        binary: 'auto',
        reset: () => {
          bids = null
          asks = null
        },
        handle: (raw): VenueMsgResult => {
          let msg: unknown
          try {
            msg = JSON.parse(raw)
          } catch {
            return null
          }
          if (typeof msg !== 'object' || msg === null) return null
          const m = msg as {
            group?: string
            success?: boolean
            error_message?: string
            errorMessage?: string
            data?: { way?: number; depths?: unknown; ms_t?: unknown } | null
          }
          if (m.group === 'System') return null // pong
          if (m.success === false) {
            return { fatal: m.error_message ?? m.errorMessage ?? 'subscribe rejected' }
          }
          const d = m.data
          if (typeof d !== 'object' || d === null || d.way === undefined) return null

          const side = parseSide(d.depths)
          if (!side) return null
          if (d.way === 1) bids = side.sort((a, b) => b[0] - a[0]).slice(0, DEPTH_LEVEL)
          else if (d.way === 2) asks = side.sort((a, b) => a[0] - b[0]).slice(0, DEPTH_LEVEL)
          else return null

          // emit only once both sides are present, like the backend
          if (!bids || !asks || bids.length === 0 || asks.length === 0) return null
          if (bids[0][0] >= asks[0][0]) return null // crossed
          const ts = Number(d.ms_t)
          return {
            bids: bids.map(([p, v]) => [p, v * mult]),
            asks: asks.map(([p, v]) => [p, v * mult]),
            ts: Number.isFinite(ts) ? ts : null,
          }
        },
      },
      opts,
    )
  },
}
