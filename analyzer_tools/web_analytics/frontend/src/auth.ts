import { useSyncExternalStore } from 'react'

// Token from GET /api/auth, kept in localStorage so a reload doesn't log out.
// client.ts attaches it to every API request and clears it on 401.

export interface AuthState {
  token: string
  tokenType: string
  name: string
}

const KEY = 'ss.auth'

// exp claim (ms) when the token is a JWT, else null (opaque tokens are
// trusted until the backend rejects them).
function jwtExpMs(token: string): number | null {
  const parts = token.split('.')
  if (parts.length !== 3) return null
  try {
    const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))
    return typeof payload.exp === 'number' ? payload.exp * 1000 : null
  } catch {
    return null
  }
}

function isExpired(s: AuthState): boolean {
  const exp = jwtExpMs(s.token)
  return exp !== null && Date.now() >= exp
}

function load(): AuthState | null {
  try {
    const raw = localStorage.getItem(KEY)
    if (raw === null) return null
    const v = JSON.parse(raw) as AuthState
    if (typeof v?.token !== 'string' || typeof v?.tokenType !== 'string') return null
    if (isExpired(v)) {
      localStorage.removeItem(KEY)
      return null
    }
    return v
  } catch {
    return null
  }
}

let state: AuthState | null = load()
const listeners = new Set<() => void>()

function emit() {
  for (const fn of listeners) fn()
}

export function getAuth(): AuthState | null {
  return state
}

export function authHeader(): Record<string, string> {
  if (state && isExpired(state)) clearAuth() // flips the app to the login page
  return state ? { Authorization: `${state.tokenType} ${state.token}` } : {}
}

export function setAuth(next: AuthState) {
  state = next
  try {
    localStorage.setItem(KEY, JSON.stringify(next))
  } catch {
    // storage blocked — session still works in-memory
  }
  emit()
}

export function clearAuth() {
  if (state === null) return
  state = null
  try {
    localStorage.removeItem(KEY)
  } catch {
    // ignore
  }
  emit()
}

export function useAuth(): AuthState | null {
  return useSyncExternalStore(
    (fn) => {
      listeners.add(fn)
      return () => listeners.delete(fn)
    },
    getAuth,
  )
}

export async function login(
  name: string,
  secret: string,
): Promise<{ ok: true } | { ok: false; error: string }> {
  let res: Response
  try {
    res = await fetch(
      `/auth?name=${encodeURIComponent(name)}&secret=${encodeURIComponent(secret)}`,
      { headers: { Accept: 'application/json' } },
    )
  } catch (err) {
    return { ok: false, error: err instanceof Error ? err.message : String(err) }
  }
  if (!res.ok) {
    return { ok: false, error: `${res.status}${res.statusText ? ` ${res.statusText}` : ''}` }
  }
  let body: { token?: unknown; token_type?: unknown }
  try {
    body = await res.json()
  } catch {
    return { ok: false, error: 'invalid response' }
  }
  if (typeof body.token !== 'string' || typeof body.token_type !== 'string') {
    return { ok: false, error: 'invalid response' }
  }
  setAuth({ token: body.token, tokenType: body.token_type, name })
  return { ok: true }
}
