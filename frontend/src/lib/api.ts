/**
 * API Client
 * Typed fetch wrapper for the EV Cluster Load FastAPI backend.
 * - Reads base URL from VITE_API_URL env var (falls back to /api/v1)
 * - Attaches Authorization header from Zustand store
 * - Retries GET/HEAD requests up to 2 times on network errors
 * - Fires a toast on non-2xx responses
 */

const BASE_URL = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '')

class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown, message: string) {
    super(message)
    this.status = status
    this.body = body
    this.name = 'ApiError'
  }
}

let _getToken: () => string | null = () => null
let _showToast: (msg: string, variant: 'error' | 'success' | 'info') => void = () => {}

/** Call once in main.tsx after store is ready */
export function initApiClient(
  getToken: () => string | null,
  showToast: (msg: string, variant: 'error' | 'success' | 'info') => void
) {
  _getToken = getToken
  _showToast = showToast
}

async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  retries = 2
): Promise<T> {
  const token = _getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const method = (init.method ?? 'GET').toUpperCase()
  const isSafe = method === 'GET' || method === 'HEAD'

  let lastErr: Error | null = null
  for (let attempt = 0; attempt <= (isSafe ? retries : 0); attempt++) {
    try {
      const res = await fetch(`${BASE_URL}${path}`, { ...init, headers })
      if (!res.ok) {
        let body: unknown = null
        try {
          body = await res.json()
        } catch {
          body = await res.text()
        }
        const message =
          (body as { detail?: string })?.detail ??
          `HTTP ${res.status}: ${res.statusText}`
        _showToast(message, 'error')
        throw new ApiError(res.status, body, message)
      }
      if (res.status === 204) return undefined as unknown as T
      return (await res.json()) as T
    } catch (err) {
      if (err instanceof ApiError) throw err
      lastErr = err as Error
      if (attempt < retries && isSafe) {
        await new Promise((r) => setTimeout(r, 300 * 2 ** attempt))
      }
    }
  }
  _showToast(lastErr?.message ?? 'Network error', 'error')
  throw lastErr
}

// ============================================================
// API Modules
// ============================================================

export interface ClusterResponse {
  transformer_kva: number
  power_factor: number
  stations: Array<{
    id: string
    name: string
    chargers: number
    kw: number
    detour: number
    latitude?: number
    longitude?: number
  }>
}

export interface ForecastResponse {
  hours: number[]
  p10: number[]
  p50: number[]
  p90: number[]
  warn: number
  critical: number
  model_version: string
}

export interface TransformerRiskResponse {
  transformer_id: string
  kva: number
  peak_p90_pct: number
  peak_hour: number
  first_warning_hour?: number
  level: 'ok' | 'warning' | 'critical'
  warn_threshold_pct: number
  crit_threshold_pct: number
}

export interface CandidateSlot {
  station: string
  station_id: string
  hour: number
  starts_in_h: number
  wait_min: number
  detour_min: number
  grid_load_pct: number
  score: number
}

export interface RecommendResponse {
  mode: string
  top3: CandidateSlot[]
}

export interface RecommendRequest {
  mode: 'fastest' | 'balanced' | 'grid_friendly'
  start_hour?: number
  horizon?: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: {
    username: string
    role: string
    cluster_id?: string
    email?: string
  }
}

export interface SimulationMetrics {
  algorithm: string
  peak_load_pct: number
  mean_wait_min: number
  overload_events: number
}

export interface MetricsSimulation {
  fcfs: SimulationMetrics
  smart: SimulationMetrics
}

export interface ReplayStartRequest {
  speed_multiplier: number
  horizon_hours: number
}

export interface ReplayStartResponse {
  session_id: string
  speed_multiplier: number
  horizon_hours: number
  started_at: string
  status: string
  total_ticks: number
  current_tick: number
}

export interface StationDetail {
  id: string
  name: string
  chargers: number
  kw: number
  detour: number
  latitude?: number
  longitude?: number
  utilization_pct?: number
  queue_count?: number
}

export interface PaginatedStations {
  items: StationDetail[]
  total: number
  page: number
  page_size: number
}

// ============================================================
// API Functions
// ============================================================

export const api = {
  clusters: {
    list: () => apiFetch<ClusterResponse[]>('/clusters'),
  },

  stations: {
    list: (params?: { cluster_id?: string; page?: number; page_size?: number }) => {
      const qs = new URLSearchParams()
      if (params?.cluster_id) qs.set('cluster_id', params.cluster_id)
      if (params?.page != null) qs.set('page', String(params.page))
      if (params?.page_size != null) qs.set('page_size', String(params.page_size))
      return apiFetch<PaginatedStations>(`/stations${qs.toString() ? `?${qs}` : ''}`)
    },
    get: (id: string) => apiFetch<StationDetail>(`/stations/${id}`),
  },

  forecast: {
    get: () => apiFetch<ForecastResponse>('/forecast'),
  },

  transformer: {
    risk: (id = 'T1') => apiFetch<TransformerRiskResponse>(`/transformer/${id}/risk`),
  },

  recommend: {
    post: (body: RecommendRequest) =>
      apiFetch<RecommendResponse>('/recommend', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
  },

  replay: {
    start: (body: ReplayStartRequest) =>
      apiFetch<ReplayStartResponse>('/replay/start', {
        method: 'POST',
        body: JSON.stringify(body),
      }),
    metrics: () => apiFetch<MetricsSimulation>('/metrics/simulation'),
  },

  auth: {
    login: (username: string, password: string) =>
      apiFetch<TokenResponse>('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password }),
      }),
    refresh: (refresh_token: string) =>
      apiFetch<TokenResponse>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token }),
      }),
    me: () => apiFetch<{ username: string; role: string; cluster_id?: string; email?: string }>('/auth/me'),
  },
}
