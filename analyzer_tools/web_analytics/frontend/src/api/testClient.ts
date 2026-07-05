// Shared helper for the endpoint test bench: run a request, time it, and read
// the body as text so any HTTP status (not just 2xx) can be displayed.

export interface TestResult {
  status: number
  statusText: string
  ok: boolean
  durationMs: number
  sizeBytes: number
  body: string
}

// Variant persisted in request history. Bodies over the cap are dropped
// (body: null) so a few large responses can't exhaust the localStorage quota.
export const HISTORY_BODY_CAP = 200_000

export interface StoredResult {
  status: number
  statusText: string
  ok: boolean
  durationMs: number
  sizeBytes: number
  body: string | null
}

export function toStoredResult(r: TestResult): StoredResult {
  return {
    status: r.status,
    statusText: r.statusText,
    ok: r.ok,
    durationMs: r.durationMs,
    sizeBytes: r.sizeBytes,
    body: r.body.length <= HISTORY_BODY_CAP ? r.body : null,
  }
}

export function fromStoredResult(s: StoredResult): TestResult {
  return { ...s, body: s.body ?? 'body not stored' }
}

export async function runRequest(
  send: () => Promise<Response>,
): Promise<{ result: TestResult | null; error: string | null }> {
  const started = performance.now()
  try {
    const res = await send()
    const body = await res.text()
    return {
      result: {
        status: res.status,
        statusText: res.statusText,
        ok: res.ok,
        durationMs: Math.round(performance.now() - started),
        sizeBytes: new Blob([body]).size,
        body,
      },
      error: null,
    }
  } catch (err) {
    // Network-level failure (backend down, proxy target unreachable, etc.)
    return {
      result: null,
      error: err instanceof Error ? err.message : String(err),
    }
  }
}
