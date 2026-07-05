import type { Exchange } from '../ws'
import type { CexAdapter } from './types'
import { binance } from './binance'
import { bybit } from './bybit'
import { okx } from './okx'
import { bitget } from './bitget'
import { coinex } from './coinex'
import { bingx } from './bingx'
import { bitmart } from './bitmart'
import { htx } from './htx'
import { lbank } from './lbank'

// Every adapter mirrors the feed documented in CEX_CONNECTIONS.md — the same
// stream the backend consumes — so books are directly comparable. Absent or
// partially supported venues are the ones whose md approach a browser cannot
// perform: mexc (protobuf), gateio (custom Origin), kucoin (CORS-blocked
// bullet-public token), bybit futures / htx futures (custom Origin), bitmart
// spot (host refuses connections outside the backend environment).
export const CEX_ADAPTERS: Partial<Record<Exchange, CexAdapter>> = {
  binance,
  bybit,
  okx,
  bitget,
  coinex,
  bingx,
  bitmart,
  htx,
  lbank,
}

export type { CexBook, CexStatus } from './types'
