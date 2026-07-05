import { useEffect, useRef, useState } from 'react'
import { CEX_ADAPTERS } from './api/cex'
import type { Exchange, Market } from './api/ws'
import { pinCard, type LiveVenueEntry } from './pinnedCards'
import type { VenueCardView } from './components/VenueCardBody'

const FLUSH_MS = 200

export interface FeedTarget {
  exchange: Exchange
  symbol: string
  market: Market
}

export const feedKey = (t: FeedTarget) => `${t.exchange}|${t.market}|${t.symbol}`

// Registry of direct venue feeds for one page: open/close/pin plus the
// ref-buffered 200ms flush that turns hot feed state into immutable card
// views. Feeds close on unmount; pinned ones are transferred out first and
// survive.
export function useVenueFeeds() {
  const [cards, setCards] = useState<VenueCardView[]>([])
  const [nowMs, setNowMs] = useState(0)
  const registryRef = useRef<Map<string, LiveVenueEntry>>(new Map())
  const dirtyRef = useRef(false)

  function open(target: FeedTarget): string {
    const key = feedKey(target)
    const existing = registryRef.current.get(key)
    if (existing) {
      existing.feed?.close()
      registryRef.current.delete(key)
    }

    const adapter = CEX_ADAPTERS[target.exchange]
    const supported = adapter !== undefined && adapter.supports(target.market)
    const entry: LiveVenueEntry = {
      key,
      exchange: target.exchange,
      symbol: target.symbol,
      market: target.market,
      host: supported ? adapter.host(target.market) : null,
      status: supported ? 'connecting' : 'unsupported',
      feed: null,
      latest: null,
      lastFlushed: null,
      frames: 0,
      flushedCount: 0,
      rate: 0,
      lastAt: 0,
    }
    registryRef.current.set(key, entry)
    dirtyRef.current = true
    if (supported) {
      // entry is per-feed: once deleted from the registry, late events from a
      // dying socket mutate a detached object nobody reads
      entry.feed = adapter.open({
        symbol: target.symbol,
        market: target.market,
        onBook: (b) => {
          entry.latest = b
          entry.frames += 1
          entry.lastAt = Date.now()
        },
        onStatus: (status, detail) => {
          entry.status = status
          entry.detail = detail
          dirtyRef.current = true
        },
      })
    }
    return key
  }

  function close(key: string) {
    const entry = registryRef.current.get(key)
    if (!entry) return
    entry.feed?.close()
    registryRef.current.delete(key)
    dirtyRef.current = true
  }

  function closeAll() {
    for (const entry of registryRef.current.values()) entry.feed?.close()
    registryRef.current.clear()
    dirtyRef.current = true
  }

  // Hands the entry (and its open socket) to the floating layer, which
  // survives page unmount and tab switches.
  function pin(key: string) {
    const entry = registryRef.current.get(key)
    if (!entry) return
    registryRef.current.delete(key)
    dirtyRef.current = true
    pinCard(entry)
  }

  useEffect(() => {
    const id = setInterval(() => {
      let changed = dirtyRef.current
      dirtyRef.current = false
      for (const e of registryRef.current.values()) {
        if (e.latest !== e.lastFlushed) {
          e.lastFlushed = e.latest
          changed = true
        }
        const delta = e.frames - e.flushedCount
        e.flushedCount = e.frames
        if (delta > 0 || e.rate > 0) {
          e.rate = Math.round(delta * (1000 / FLUSH_MS))
          changed = true
        }
      }
      if (changed) {
        setCards(
          [...registryRef.current.values()].map((e) => ({
            key: e.key,
            exchange: e.exchange,
            symbol: e.symbol,
            market: e.market,
            host: e.host,
            status: e.status,
            detail: e.detail,
            book: e.latest,
            frames: e.frames,
            rate: e.rate,
            lastAt: e.lastAt,
          })),
        )
      }
      // gated: with no feeds the page renders exactly as before
      if (registryRef.current.size > 0) setNowMs(Date.now())
    }, FLUSH_MS)
    return () => {
      clearInterval(id)
      for (const entry of registryRef.current.values()) entry.feed?.close()
      registryRef.current.clear()
    }
  }, [])

  return { cards, nowMs, open, close, closeAll, pin }
}
