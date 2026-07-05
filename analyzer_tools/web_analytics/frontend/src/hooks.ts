import { useEffect, useState, type SetStateAction } from 'react'
import type { StoredResult } from './api/testClient'

function load<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? fallback : (JSON.parse(raw) as T)
  } catch {
    return fallback
  }
}

// useState mirrored to localStorage, so form inputs survive reloads.
// State is tracked together with its key: if the key changes while the
// component instance is reused (e.g. same tester type across two tabs), the
// new key's value is loaded instead of writing the old key's state over it.
export function usePersistedState<T>(key: string, initial: T) {
  const [entry, setEntry] = useState(() => ({ key, value: load(key, initial) }))

  if (entry.key !== key) {
    setEntry({ key, value: load(key, initial) })
  }

  useEffect(() => {
    try {
      localStorage.setItem(entry.key, JSON.stringify(entry.value))
    } catch {
      // storage full or blocked — state still works in-memory
    }
  }, [entry])

  function setValue(action: SetStateAction<T>) {
    setEntry((prev) => ({
      key: prev.key,
      value:
        typeof action === 'function' ? (action as (p: T) => T)(prev.value) : action,
    }))
  }

  return [entry.value, setValue] as const
}

export interface HistoryEntry<T> {
  at: number
  data: T
  // stored response; null = network failure; absent on pre-feature entries
  result?: StoredResult | null
}

// Rolling request history in localStorage. Consecutive duplicates (same form
// snapshot) replace the head entry, keeping the newest result. T must be
// JSON-plain.
export function useRequestHistory<T>(key: string, limit = 10) {
  const [entries, setEntries] = usePersistedState<HistoryEntry<T>[]>(key, [])
  const list = Array.isArray(entries) ? entries : []

  function push(data: T, result: StoredResult | null) {
    const entry = { at: Date.now(), data, result }
    setEntries((prev) => {
      const cur = Array.isArray(prev) ? prev : []
      if (cur.length > 0 && JSON.stringify(cur[0].data) === JSON.stringify(data)) {
        return [entry, ...cur.slice(1)]
      }
      return [entry, ...cur].slice(0, limit)
    })
  }

  function clear() {
    setEntries([])
  }

  return { entries: list, push, clear }
}
