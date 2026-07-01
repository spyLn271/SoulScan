// Shared helper for the endpoint test bench: run a request, time it, and read
// the body as text so any HTTP status (not just 2xx) can be displayed.

export interface TestResult {
  status: number
  statusText: string
  ok: boolean
  durationMs: number
  body: string
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
