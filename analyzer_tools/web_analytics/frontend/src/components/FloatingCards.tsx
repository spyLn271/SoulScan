import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import {
  bumpPinned,
  closePinned,
  movePinned,
  pinnedEntries,
  pinnedVersion,
  subscribePinned,
} from '../pinnedCards'
import { DOT_BY_STATUS, VenueCardBody, type VenueCardView } from './VenueCardBody'

const FLUSH_MS = 200

interface FloatView extends VenueCardView {
  x: number
  y: number
  z: number
}

function buildViews(): FloatView[] {
  return pinnedEntries().map((e) => ({
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
    x: e.x,
    y: e.y,
    z: e.z,
  }))
}

// App-level layer rendering pinned venue cards as draggable floating windows
// that survive page/tab switches. Desktop-only (hidden ≤880px via CSS).
export function FloatingCards() {
  const version = useSyncExternalStore(subscribePinned, pinnedVersion)
  const [views, setViews] = useState<FloatView[]>([])

  useEffect(() => {
    setViews(buildViews())
    const id = setInterval(() => {
      const entries = pinnedEntries()
      if (entries.length === 0) return
      for (const e of entries) {
        if (e.latest !== e.lastFlushed) e.lastFlushed = e.latest
        const delta = e.frames - e.flushedCount
        e.flushedCount = e.frames
        if (delta > 0 || e.rate > 0) e.rate = Math.round(delta * (1000 / FLUSH_MS))
      }
      setViews(buildViews())
    }, FLUSH_MS)
    return () => clearInterval(id)
  }, [version])

  if (views.length === 0) return null

  return (
    <div className="float-layer">
      {views.map((v) => (
        <FloatCard key={v.key} v={v} />
      ))}
    </div>
  )
}

function FloatCard({ v }: { v: FloatView }) {
  const [dragPos, setDragPos] = useState<{ x: number; y: number } | null>(null)
  const offRef = useRef<{ dx: number; dy: number } | null>(null)

  // hand off from local drag position back to the store position once the
  // store has caught up — avoids a one-frame jump after drop
  useEffect(() => {
    if (dragPos && dragPos.x === v.x && dragPos.y === v.y) setDragPos(null)
  }, [dragPos, v.x, v.y])

  const x = dragPos?.x ?? v.x
  const y = dragPos?.y ?? v.y

  return (
    <div
      className="float-card"
      style={{ left: x, top: y, zIndex: v.z }}
      onPointerDown={() => bumpPinned(v.key)}
    >
      <div
        className="float-card__head"
        onPointerDown={(e) => {
          if ((e.target as HTMLElement).closest('button')) return
          offRef.current = { dx: e.clientX - x, dy: e.clientY - y }
          e.currentTarget.setPointerCapture(e.pointerId)
        }}
        onPointerMove={(e) => {
          const o = offRef.current
          if (!o) return
          setDragPos({ x: e.clientX - o.dx, y: e.clientY - o.dy })
        }}
        onPointerUp={(e) => {
          const o = offRef.current
          if (!o) return
          offRef.current = null
          e.currentTarget.releasePointerCapture(e.pointerId)
          movePinned(v.key, e.clientX - o.dx, e.clientY - o.dy)
        }}
      >
        <span className={`dot dot--${DOT_BY_STATUS[v.status]}`} title={v.status} />
        <span className="float-card__title">
          {v.exchange} · {v.market} · {v.symbol}
        </span>
        <button
          type="button"
          className="btn btn--ghost btn--xs"
          onClick={() => closePinned(v.key)}
        >
          ✕
        </button>
      </div>
      <VenueCardBody view={v} depth={10} />
    </div>
  )
}
