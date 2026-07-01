import { apiGet } from './client'

export interface HealthResponse {
  status: string
}

// Expects the axum backend to expose `GET /api/health` returning
// `{ "status": "ok" }`. Used by the header status pill.
export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>('/health')
}
