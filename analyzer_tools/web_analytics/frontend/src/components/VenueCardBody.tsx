import type { Exchange, Market } from '../api/ws'
import type { CexBook, CexStatus } from '../api/cex'
import { Ladder } from './Ladder'
import { fmtTs } from '../format/time'

// Immutable render snapshot of a direct venue feed — used by the in-page
// cards and the floating pinned cards.
export interface VenueCardView {
  key: string
  exchange: Exchange
  symbol: string
  market: Market
  host: string | null
  status: CexStatus
  detail?: string
  book: CexBook | null
  frames: number
  rate: number
  lastAt: number
}

export const DOT_BY_STATUS: Record<CexStatus, string> = {
  connecting: 'connecting',
  live: 'connected',
  error: 'error',
  closed: 'disconnected',
  unsupported: 'disconnected',
}

export function VenueCardBody({ view: c, depth = 15 }: { view: VenueCardView; depth?: number }) {
  return (
    <>
      {c.status === 'unsupported' && <p className="empty">direct feed unavailable</p>}
      {c.status === 'error' && (
        <p className="empty note">feed error{c.detail ? ` — ${c.detail}` : ''}</p>
      )}
      {c.book === null && c.status === 'connecting' && <p className="empty">connecting</p>}
      {c.book === null && c.status === 'live' && <p className="empty">no frames</p>}
      {c.book === null && c.status === 'closed' && <p className="empty">closed</p>}

      {c.book !== null && (
        <>
          <div className="stats">
            <div className="stat">
              <span className="stat__label">frames</span>
              <span className="stat__value">{c.frames.toLocaleString('en-US')}</span>
            </div>
            <div className="stat">
              <span className="stat__label">rate</span>
              <span className="stat__value">{c.rate}/s</span>
            </div>
            <div className="stat">
              <span className="stat__label">last frame</span>
              <span className="stat__value">
                {c.book.ts !== null ? fmtTs(c.book.ts) : '—'}
              </span>
            </div>
            <div className="stat">
              <span className="stat__label">levels</span>
              <span className="stat__value">
                {c.book.asks.length} × {c.book.bids.length}
              </span>
            </div>
          </div>

          {c.exchange === 'okx' && c.market === 'futures' && (
            <p className="empty note">sizes in contracts</p>
          )}

          <Ladder book={c.book} depth={depth} />
        </>
      )}
    </>
  )
}
