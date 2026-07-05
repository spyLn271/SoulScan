export type HttpMethod = 'GET' | 'POST' | 'WS'

export function EndpointChip({ method, path }: { method: HttpMethod; path: string }) {
  return (
    <span className="endpoint">
      <span className={`method method--${method.toLowerCase()}`}>{method}</span>
      <code className="endpoint__path">{path}</code>
    </span>
  )
}
