import { authHeader, clearAuth } from '../auth'

const API_BASE = '/api'

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// Token expired/revoked/missing — drop it so the app returns to the login
// page. The backend answers auth failures with 400 (axum-jwt-example style),
// which is also what malformed tester requests get — so on 400 only the
// known auth-error bodies log out, never domain errors.
const AUTH_ERROR_MESSAGES = new Set([
  'Invalid token',
  'Missing credentials',
  'Wrong credentials',
])

async function checkUnauthorized(res: Response) {
  if (res.status === 401 || res.status === 403) {
    clearAuth()
    return
  }
  if (res.status === 400) {
    try {
      const body = (await res.clone().json()) as { error?: unknown }
      if (typeof body.error === 'string' && AUTH_ERROR_MESSAGES.has(body.error)) {
        clearAuth()
      }
    } catch {
      // not JSON — a domain error, not an auth rejection
    }
  }
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json', ...authHeader() },
    ...init,
  })
  await checkUnauthorized(res)
  if (!res.ok) {
    throw new ApiError(
      `GET ${path} failed: ${res.status} ${res.statusText}`,
      res.status,
    )
  }
  return res.json() as Promise<T>
}

export async function apiPostRaw(
  path: string,
  jsonBody: string,
): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...authHeader(),
    },
    body: jsonBody,
  })
  await checkUnauthorized(res)
  return res
}

export async function apiGetRaw(path: string): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json', ...authHeader() },
  })
  await checkUnauthorized(res)
  return res
}
