// Client side of the order-book WebSocket (`.route("/ws", any(handler))`).
//
// serde wire format notes — every enum on the Rust side is INTERNALLY tagged,
// so unit variants serialize as objects, not bare strings:
//
//   ClientMessage  tag = "action"         -> {"action":"subscribe", ...fields}
//   Exchange       tag = "exchange_type"  -> {"exchange_type":"binance"}
//   Market         tag = "market_type"    -> {"market_type":"spot"}

export const EXCHANGES = [
  'binance',
  'bybit',
  'okx',
  'mexc',
  'bingx',
  'bitget',
  'bitmart',
  'coinex',
  'htx',
  'lbank',
  'gateio',
  'kucoin',
] as const
export type Exchange = (typeof EXCHANGES)[number]

export const MARKETS = ['spot', 'futures'] as const
export type Market = (typeof MARKETS)[number]

export interface StreamId {
  exchange: Exchange
  symbol: string
  market: Market
}

// Largest value a u64 can hold (latency field).
export const U64_MAX = (1n << 64n) - 1n

// latency is u64 — serialized as a bare integer literal (same reasoning as
// the SOR amount: JSON.stringify can't encode bigint).
export function buildSubscribe(p: StreamId & { latency: bigint }): string {
  return (
    '{' +
    '"action":"subscribe",' +
    `"exchange":{"exchange_type":${JSON.stringify(p.exchange)}},` +
    `"symbol":${JSON.stringify(p.symbol)},` +
    `"market":{"market_type":${JSON.stringify(p.market)}},` +
    `"latency":${p.latency.toString()}` +
    '}'
  )
}

export function buildUnsubscribe(p: StreamId): string {
  return (
    '{' +
    '"action":"unsubscribe",' +
    `"exchange":{"exchange_type":${JSON.stringify(p.exchange)}},` +
    `"symbol":${JSON.stringify(p.symbol)},` +
    `"market":{"market_type":${JSON.stringify(p.market)}}` +
    '}'
  )
}

// Server -> client frame:
//   pub struct OrderBook { timestamp_ms: u64, asks: Vec<Vec<f64>>, bids: Vec<Vec<f64>> }
// Note: no exchange/symbol/market in the payload, so frames from multiple
// subscriptions on one socket cannot be told apart client-side.
export interface OrderBookMsg {
  timestamp_ms: number
  asks: number[][]
  bids: number[][]
}

// f64 levels fit JS numbers natively, so plain JSON.parse is correct here
// (and fast — this runs on every frame).
export function parseOrderBook(raw: string): OrderBookMsg | null {
  try {
    const v: unknown = JSON.parse(raw)
    if (
      typeof v === 'object' &&
      v !== null &&
      typeof (v as OrderBookMsg).timestamp_ms === 'number' &&
      Array.isArray((v as OrderBookMsg).asks) &&
      Array.isArray((v as OrderBookMsg).bids)
    ) {
      return v as OrderBookMsg
    }
  } catch {
    // not JSON — caller logs the raw text
  }
  return null
}
