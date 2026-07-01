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

export async function apiGet<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json' },
    ...init,
  })
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
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: jsonBody,
  })
}

// GET returning the raw Response so the caller can inspect status + body for
// any HTTP status (the test bench needs to show failures too, not just 2xx).
export async function apiGetRaw(path: string): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    headers: { Accept: 'application/json' },
  })
}
