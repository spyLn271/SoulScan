import { type FormEvent } from 'react'
import { EXCHANGES, MARKETS, type Exchange, type Market } from '../api/ws'
import { DOT_BY_STATUS, VenueCardBody } from '../components/VenueCardBody'
import { usePersistedState } from '../hooks'
import { useVenueFeeds } from '../useVenueFeeds'

const QUOTES = ['USDT', 'USDC']

// Backend-free market watch: open any number of direct venue books.
export function BookWatch() {
  const [exchange, setExchange] = usePersistedState<Exchange>('ss.watch.exchange', 'binance')
  const [market, setMarket] = usePersistedState<Market>('ss.watch.market', 'spot')
  const [base, setBase] = usePersistedState('ss.watch.base', 'BTC')
  const [quote, setQuote] = usePersistedState('ss.watch.quote', 'USDT')

  const feeds = useVenueFeeds()
  const canAdd = base.trim() !== '' && quote.trim() !== ''

  function onAdd(e: FormEvent) {
    e.preventDefault()
    if (!canAdd) return
    const symbol = `${base.trim()}${quote.trim()}`.toUpperCase()
    feeds.open({ exchange, symbol, market })
  }

  return (
    <div className="watch">
      <form className="panel" onSubmit={onAdd}>
        <div className="conn-row">
          <label className="field">
            <span className="field__label">exchange</span>
            <select
              value={exchange}
              onChange={(e) => setExchange(e.target.value as Exchange)}
            >
              {EXCHANGES.map((x) => (
                <option key={x} value={x}>
                  {x}
                </option>
              ))}
            </select>
          </label>
          <div className="field">
            <span className="field__label">market</span>
            <div className="seg">
              {MARKETS.map((m) => (
                <button
                  type="button"
                  key={m}
                  className={`seg__btn ${market === m ? 'seg__btn--active' : ''}`}
                  onClick={() => setMarket(m)}
                >
                  {m}
                </button>
              ))}
            </div>
          </div>
          <label className="field">
            <span className="field__label">base</span>
            <input
              value={base}
              onChange={(e) => setBase(e.target.value)}
              placeholder="BTC"
              spellCheck={false}
            />
          </label>
          <label className="field">
            <span className="field__label">quote</span>
            <input
              list="watch-quotes"
              value={quote}
              onChange={(e) => setQuote(e.target.value)}
              placeholder="USDT"
              spellCheck={false}
            />
            <datalist id="watch-quotes">
              {QUOTES.map((q) => (
                <option key={q} value={q} />
              ))}
            </datalist>
          </label>
          <button className="btn btn--inline" type="submit" disabled={!canAdd}>
            add
          </button>
        </div>
      </form>

      {feeds.cards.length === 0 ? (
        <p className="empty">no books</p>
      ) : (
        <div className="watch-grid">
          {feeds.cards.map((c) => (
            <div key={c.key} className="panel">
              <div className="panel__head">
                <h2>
                  {c.exchange} · {c.market} · {c.symbol}
                </h2>
                <div className="panel__tools">
                  {c.status !== 'unsupported' && (
                    <button
                      type="button"
                      className="btn btn--ghost btn--xs"
                      onClick={() => feeds.pin(c.key)}
                    >
                      pin
                    </button>
                  )}
                  <button
                    type="button"
                    className="btn btn--ghost btn--xs"
                    onClick={() => feeds.close(c.key)}
                  >
                    ✕
                  </button>
                  <span
                    className={`dot dot--${DOT_BY_STATUS[c.status]}`}
                    title={c.status}
                  />
                </div>
              </div>
              <VenueCardBody view={c} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
