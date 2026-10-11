/**
 * TanStack Query hooks for all server state.
 * Stale times are tuned to domain semantics:
 *   - Cluster topology: 5 minutes (rarely changes)
 *   - Forecast: 2 minutes (updated each model run)
 *   - Transformer risk: 1 minute (threshold-sensitive)
 *   - Recommendation: 30 seconds (driven by live load)
 *   - Simulation metrics: 3 minutes
 */
import { useQuery, useMutation, useQueryClient, QueryClient } from '@tanstack/react-query'
import { api, type RecommendRequest, type ForecastResponse } from './api'

// Query key factory (ensures typed cache invalidation)
export const queryKeys = {
  clusters: () => ['clusters'] as const,
  stations: (params?: Record<string, unknown>) => ['stations', params] as const,
  station: (id: string) => ['stations', id] as const,
  forecast: () => ['forecast'] as const,
  transformerRisk: (id = 'T1') => ['transformer', id, 'risk'] as const,
  recommendations: (mode: string) => ['recommendations', mode] as const,
  simulationMetrics: () => ['simulation', 'metrics'] as const,
  authMe: () => ['auth', 'me'] as const,
}

// ── Cluster ──────────────────────────────────────────────────────────────────
export function useClusters() {
  return useQuery({
    queryKey: queryKeys.clusters(),
    queryFn: () => api.clusters.list(),
    staleTime: 5 * 60 * 1000,
  })
}

// ── Stations ─────────────────────────────────────────────────────────────────
export function useStations(params?: { cluster_id?: string; page?: number; page_size?: number }) {
  return useQuery({
    queryKey: queryKeys.stations(params),
    queryFn: () => api.stations.list(params),
    staleTime: 5 * 60 * 1000,
  })
}

export function useStation(id: string) {
  return useQuery({
    queryKey: queryKeys.station(id),
    queryFn: () => api.stations.get(id),
    staleTime: 5 * 60 * 1000,
    enabled: Boolean(id),
  })
}

// ── Forecast ─────────────────────────────────────────────────────────────────
export function useForecast() {
  return useQuery({
    queryKey: queryKeys.forecast(),
    queryFn: () => api.forecast.get(),
    staleTime: 2 * 60 * 1000,
    // Refresh every 2 minutes in background
    refetchInterval: 2 * 60 * 1000,
  })
}

// ── Transformer Risk ──────────────────────────────────────────────────────────
export function useTransformerRisk(id = 'T1') {
  return useQuery({
    queryKey: queryKeys.transformerRisk(id),
    queryFn: () => api.transformer.risk(id),
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  })
}

// ── Recommendations ───────────────────────────────────────────────────────────
export function useRecommendations(req: RecommendRequest) {
  return useQuery({
    queryKey: queryKeys.recommendations(req.mode),
    queryFn: () => api.recommend.post(req),
    staleTime: 30 * 1000,
    // POST acting as a query — no automatic refetch
  })
}

// ── Simulation Metrics ────────────────────────────────────────────────────────
export function useSimulationMetrics() {
  return useQuery({
    queryKey: queryKeys.simulationMetrics(),
    queryFn: () => api.replay.metrics(),
    staleTime: 3 * 60 * 1000,
  })
}

// ── Auth ──────────────────────────────────────────────────────────────────────
export function useMe(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.authMe(),
    queryFn: () => api.auth.me(),
    enabled,
    staleTime: 5 * 60 * 1000,
    retry: false,
  })
}

export function useLoginMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      api.auth.login(username, password),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.authMe() })
    },
  })
}

// ── WebSocket → Query Cache injection ────────────────────────────────────────
/**
 * Call this from useWebSocket when a message of type 'forecast_update' arrives.
 * Patches the forecast query cache directly without issuing a refetch.
 */
export function patchForecastCache(qc: QueryClient, patch: Partial<ForecastResponse>) {
  qc.setQueryData<ForecastResponse>(queryKeys.forecast(), (old) => {
    if (!old) return old
    return { ...old, ...patch }
  })
}
