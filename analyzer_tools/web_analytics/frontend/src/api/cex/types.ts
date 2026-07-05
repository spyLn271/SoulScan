import type { Market } from '../ws'

// Normalized book pushed by a direct venue feed. ts = venue event time (ms)
// when the feed carries one, else null (caller falls back to arrival time).
export interface CexBook {
  asks: number[][]
  bids: number[][]
  ts: number | null
}

export type CexStatus = 'connecting' | 'live' | 'error' | 'closed' | 'unsupported'

export interface CexFeedOpts {
  symbol: string
  market: Market
  onBook: (book: CexBook) => void
  onStatus: (status: CexStatus, detail?: string) => void
  // Terse caveat surfaced on the card (e.g. 'sizes in contracts' when a
  // required multiplier can't be fetched).
  onNote?: (note: string) => void
}

export interface CexFeedHandle {
  close(): void
}

export interface CexAdapter {
  supports(market: Market): boolean
  host(market: Market): string
  open(opts: CexFeedOpts): CexFeedHandle
}
