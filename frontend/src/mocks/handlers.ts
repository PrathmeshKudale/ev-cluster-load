/**
 * MSW request handlers — mirrors the real FastAPI API v1.
 * Enabled when VITE_USE_MOCKS=true (or when backend is unavailable).
 */
import { http, HttpResponse } from 'msw'
import { forecastFixture } from '@/fixtures/forecastFixture'
import { clusterFixture } from '@/fixtures/clusterFixture'
import { stationsFixture } from '@/fixtures/stationsFixture'
import { transformerFixture } from '@/fixtures/transformerFixture'
import { recommendationFixture } from '@/fixtures/recommendationFixture'
import { replayFixture } from '@/fixtures/replayFixture'

const BASE = '/api/v1'

export const handlers = [
  // GET /api/v1/clusters
  http.get(`${BASE}/clusters`, () => {
    return HttpResponse.json([
      {
        transformer_kva: 100.0,
        power_factor: 0.95,
        stations: clusterFixture.stations.map((s) => ({
          id: s.id,
          name: s.name,
          chargers: s.chargers,
          kw: s.kw,
          detour: s.detour_min,
          latitude: s.latitude,
          longitude: s.longitude,
        })),
      },
    ])
  }),

  // GET /api/v1/stations
  http.get(`${BASE}/stations`, ({ request }) => {
    const url = new URL(request.url)
    const page = parseInt(url.searchParams.get('page') ?? '1', 10)
    const pageSize = parseInt(url.searchParams.get('page_size') ?? '10', 10)
    const items = stationsFixture.map((s) => ({
      id: s.id,
      name: s.name,
      chargers: s.chargers_count,
      kw: s.kw_per_charger,
      detour: s.detour_min,
      latitude: s.latitude,
      longitude: s.longitude,
      utilization_pct: s.utilization_percent,
      queue_count: s.erlang_c_wait_min > 5 ? 3 : 0,
    }))
    return HttpResponse.json({
      items,
      total: items.length,
      page,
      page_size: pageSize,
    })
  }),

  // GET /api/v1/stations/:id
  http.get(`${BASE}/stations/:id`, ({ params }) => {
    const station = stationsFixture.find((s) => s.id === params.id)
    if (!station) return HttpResponse.json({ detail: 'Station not found' }, { status: 404 })
    return HttpResponse.json({
      id: station.id,
      name: station.name,
      chargers: station.chargers_count,
      kw: station.kw_per_charger,
      detour: station.detour_min,
      latitude: station.latitude,
      longitude: station.longitude,
      utilization_pct: station.utilization_percent,
    })
  }),

  // GET /api/v1/forecast
  http.get(`${BASE}/forecast`, () => {
    return HttpResponse.json({
      hours: forecastFixture.hours,
      p10: forecastFixture.p10,
      p50: forecastFixture.p50,
      p90: forecastFixture.p90,
      warn: forecastFixture.warn_limit_pct,
      critical: forecastFixture.crit_limit_pct,
      model_version: 'lightgbm_quantile_conformal_v1_mock',
    })
  }),

  // GET /api/v1/transformer/:id/risk
  http.get(`${BASE}/transformer/:id/risk`, () => {
    return HttpResponse.json({
      transformer_id: transformerFixture.transformer_id,
      kva: transformerFixture.rating_kva,
      peak_p90_pct: 86.5,
      peak_hour: 18,
      first_warning_hour: 17,
      level: 'warning',
      warn_threshold_pct: transformerFixture.warn_threshold_pct,
      crit_threshold_pct: transformerFixture.crit_threshold_pct,
    })
  }),

  // POST /api/v1/recommend
  http.post(`${BASE}/recommend`, async ({ request }) => {
    const body = (await request.json()) as { mode: string }
    return HttpResponse.json({
      mode: body.mode ?? 'balanced',
      top3: recommendationFixture.top3.map((r, i) => ({
        station: r.station_name,
        station_id: r.station_id,
        hour: 15 + i,
        starts_in_h: r.starts_in_h,
        wait_min: r.wait_min,
        detour_min: r.detour_min,
        grid_load_pct: r.grid_load_pct,
        score: r.score,
      })),
    })
  }),

  // GET /api/v1/metrics/simulation
  http.get(`${BASE}/metrics/simulation`, () => {
    const m = replayFixture.metrics
    return HttpResponse.json({
      fcfs: {
        algorithm: 'FCFS',
        peak_load_pct: 104.0,
        mean_wait_min: m.fcfs.mean_wait_min,
        overload_events: 4,
      },
      smart: {
        algorithm: 'SmartDispatch',
        peak_load_pct: 86.5,
        mean_wait_min: m.smart.mean_wait_min,
        overload_events: 0,
      },
    })
  }),

  // POST /api/v1/replay/start
  http.post(`${BASE}/replay/start`, async ({ request }) => {
    const body = (await request.json()) as { speed_multiplier?: number; horizon_hours?: number }
    return HttpResponse.json({
      session_id: `replay-mock-${Date.now()}`,
      speed_multiplier: body.speed_multiplier ?? 60,
      horizon_hours: body.horizon_hours ?? 24,
      started_at: new Date().toISOString(),
      status: 'running',
      total_ticks: (body.horizon_hours ?? 24) * 60,
      current_tick: 0,
    })
  }),

  // POST /api/v1/auth/login
  http.post(`${BASE}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { username: string; password: string }
    const roles: Record<string, { role: string; cluster_id?: string }> = {
      judge_demo: { role: 'judge' },
      operator_c1: { role: 'operator', cluster_id: 'C1' },
      operator_c2: { role: 'operator', cluster_id: 'C2' },
      driver_demo: { role: 'driver' },
    }
    const userInfo = roles[body.username]
    if (!userInfo) {
      return HttpResponse.json({ detail: 'Invalid credentials' }, { status: 401 })
    }
    const mockToken = `mock.jwt.${body.username}`
    return HttpResponse.json({
      access_token: mockToken,
      refresh_token: `mock.refresh.${body.username}`,
      token_type: 'bearer',
      expires_in: 900,
      user: {
        username: body.username,
        role: userInfo.role,
        cluster_id: userInfo.cluster_id ?? null,
        email: `${body.username}@cluster.ev`,
      },
    })
  }),

  // POST /api/v1/auth/refresh
  http.post(`${BASE}/auth/refresh`, async ({ request }) => {
    const body = (await request.json()) as { refresh_token: string }
    const username = body.refresh_token.replace('mock.refresh.', '')
    return HttpResponse.json({
      access_token: `mock.jwt.${username}.refreshed`,
      refresh_token: body.refresh_token,
      token_type: 'bearer',
      expires_in: 900,
      user: { username, role: 'driver', cluster_id: null, email: null },
    })
  }),

  // GET /api/v1/auth/me
  http.get(`${BASE}/auth/me`, ({ request }) => {
    const auth = request.headers.get('Authorization') ?? ''
    const token = auth.replace('Bearer ', '')
    if (!token.startsWith('mock.jwt.')) {
      return HttpResponse.json({ detail: 'Not authenticated' }, { status: 401 })
    }
    const username = token.replace('mock.jwt.', '').replace('.refreshed', '')
    const roles: Record<string, string> = {
      judge_demo: 'judge',
      operator_c1: 'operator',
      operator_c2: 'operator',
      driver_demo: 'driver',
    }
    return HttpResponse.json({
      username,
      role: roles[username] ?? 'driver',
      cluster_id: username === 'operator_c1' ? 'C1' : username === 'operator_c2' ? 'C2' : null,
      email: `${username}@cluster.ev`,
    })
  }),
]
