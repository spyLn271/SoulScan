function trimZeros(s: string): string {
  return s.includes('.') ? s.replace(/0+$/, '').replace(/\.$/, '') : s
}

// Sensible for 43250.5 and for 1.2e-8 alike.
export function fmtNum(x: number): string {
  if (!Number.isFinite(x)) return String(x)
  const a = Math.abs(x)
  if (a === 0) return '0'
  if (a >= 1000) return x.toLocaleString('en-US', { maximumFractionDigits: 2 })
  if (a >= 1) return trimZeros(x.toFixed(4))
  const leadingZeros = Math.min(18, Math.max(0, -Math.floor(Math.log10(a)) - 1))
  return trimZeros(x.toFixed(leadingZeros + 6))
}

interface Props {
  book: { asks: number[][]; bids: number[][] }
  depth?: number
}

export function Ladder({ book, depth = 15 }: Props) {
  const asks = book.asks.slice(0, depth)
  const bids = book.bids.slice(0, depth)

  let maxQty = 0
  for (const [, q = 0] of [...asks, ...bids]) maxQty = Math.max(maxQty, q)

  const bestAsk = asks[0]?.[0]
  const bestBid = bids[0]?.[0]
  const spread =
    bestAsk !== undefined && bestBid !== undefined ? bestAsk - bestBid : null
  const mid =
    bestAsk !== undefined && bestBid !== undefined ? (bestAsk + bestBid) / 2 : null

  const row = (level: number[], side: 'ask' | 'bid', key: string) => {
    const [price = 0, qty = 0] = level
    const pct = maxQty > 0 ? (qty / maxQty) * 100 : 0
    const tint = side === 'ask' ? 'var(--ob-ask-tint)' : 'var(--ob-bid-tint)'
    return (
      <div
        key={key}
        className={`ob-row ob-row--${side}`}
        style={{
          background: `linear-gradient(to left, ${tint} ${pct}%, transparent ${pct}%)`,
        }}
      >
        <span className="ob-price">{fmtNum(price)}</span>
        <span className="ob-qty">{fmtNum(qty)}</span>
      </div>
    )
  }

  return (
    <div className="ob">
      <div className="ob-head">
        <span>price</span>
        <span className="ob-qty">qty</span>
      </div>
      {/* asks reversed so the best ask sits directly above the spread */}
      {[...asks].reverse().map((l, i) => row(l, 'ask', `a${asks.length - i}`))}
      {spread !== null && mid !== null && mid > 0 && (
        <div className="ob-spread">
          spread {fmtNum(spread)} ({((spread / mid) * 100).toFixed(3)}%)
        </div>
      )}
      {bids.map((l, i) => row(l, 'bid', `b${i}`))}
    </div>
  )
}
