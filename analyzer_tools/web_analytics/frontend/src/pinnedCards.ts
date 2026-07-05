import type { Exchange, Market } from './api/ws'
import type { CexBook, CexStatus } from './api/cex'

// A live direct-venue feed with all its mutable hot state. Owned by the
// orderbooks page while unpinned; pinning TRANSFERS the same object here so
// the socket keeps streaming while the page unmounts.
export interface LiveVenueEntry {
  key: string
  exchange: Exchange
  symbol: string
  market: Market
  host: string | null
  status: CexStatus
  detail?: string
  note?: string
  feed: { close(): void } | null
  latest: CexBook | null
  lastFlushed: CexBook | null
  frames: number
  flushedCount: number
  rate: number
  lastAt: number
}

export interface PinnedEntry extends LiveVenueEntry {
  x: number
  y: number
  z: number
}

const pinned: PinnedEntry[] = []
let version = 0
let zTop = 100
const listeners = new Set<() => void>()

function emit() {
  version += 1
  for (const fn of listeners) fn()
}

export function subscribePinned(fn: () => void): () => void {
  listeners.add(fn)
  return () => listeners.delete(fn)
}

export function pinnedVersion(): number {
  return version
}

export function pinnedEntries(): readonly PinnedEntry[] {
  return pinned
}

const POS_KEY = 'ss.pin.pos'

function loadPositions(): Record<string, { x: number; y: number }> {
  try {
    const raw = localStorage.getItem(POS_KEY)
    const v = raw === null ? {} : JSON.parse(raw)
    return typeof v === 'object' && v !== null ? v : {}
  } catch {
    return {}
  }
}

function savePosition(key: string, x: number, y: number) {
  try {
    const all = loadPositions()
    all[key] = { x, y }
    localStorage.setItem(POS_KEY, JSON.stringify(all))
  } catch {
    // storage full or blocked — position just won't persist
  }
}

const clamp = (v: number, lo: number, hi: number) => Math.min(Math.max(v, lo), hi)

// Takes ownership of the entry (and its open socket). Re-pinning the same
// key replaces the previous pinned feed.
export function pinCard(entry: LiveVenueEntry): void {
  const i = pinned.findIndex((p) => p.key === entry.key)
  if (i >= 0) {
    pinned[i].feed?.close()
    pinned.splice(i, 1)
  }
  const saved = loadPositions()[entry.key]
  const n = pinned.length
  const x = clamp(
    saved?.x ?? window.innerWidth - 300 - 32 - n * 24,
    8,
    Math.max(8, window.innerWidth - 120),
  )
  const y = clamp(saved?.y ?? 76 + n * 28, 8, Math.max(8, window.innerHeight - 80))
  pinned.push(Object.assign(entry, { x, y, z: ++zTop }))
  emit()
}

export function closePinned(key: string): void {
  const i = pinned.findIndex((p) => p.key === key)
  if (i < 0) return
  pinned[i].feed?.close()
  pinned.splice(i, 1)
  emit()
}

export function movePinned(key: string, x: number, y: number): void {
  const p = pinned.find((e) => e.key === key)
  if (!p) return
  p.x = x
  p.y = y
  savePosition(key, x, y)
  emit()
}

export function bumpPinned(key: string): void {
  const p = pinned.find((e) => e.key === key)
  if (p && p.z !== zTop) {
    p.z = ++zTop
    emit()
  }
}
