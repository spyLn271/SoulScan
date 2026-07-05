import type { Exchange } from '../ws'
import type { CexAdapter } from './types'
import { binance } from './binance'
import { bybit } from './bybit'
import { okx } from './okx'
import { bitget } from './bitget'

// Venues absent from this map can't be reached from a browser (Origin locks,
// CORS-blocked token handshakes, protobuf) or await a DecompressionStream
// adapter — the card shows them as unsupported.
export const CEX_ADAPTERS: Partial<Record<Exchange, CexAdapter>> = {
  binance,
  bybit,
  okx,
  bitget,
}

export type { CexBook, CexStatus } from './types'
