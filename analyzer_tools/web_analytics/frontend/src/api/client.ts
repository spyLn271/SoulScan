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

// Token expired or revoked — drop it so the app returns to the login page.
function checkUnauthorized(res: Response) {
  if (res.status === 401) clearAuth()
}

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json', ...authHeader() },
    ...init,
  })
  checkUnauthorized(res)
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
  checkUnauthorized(res)
  return res
}

export async function apiGetRaw(path: string): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json', ...authHeader() },
  })
  checkUnauthorized(res)
  return res
}
