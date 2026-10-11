export interface CandidateRecommendation {
  rank: number
  station_id: string
  station_name: string
  hour: number
  starts_in_h: number
  available_bays: number
  total_bays: number
  charger_kw: number
  wait_min: number
  detour_min: number
  grid_load_pct: number
  score: number
  score_breakdown: {
    wait_component: number
    detour_component: number
    imbalance_component: number
    risk_component: number
    weights: {
      wait: number
      detour: number
      balance: number
      risk: number
    }
  }
  why_reason: string
}

export interface RecommendationFixture {
  mode: 'fastest' | 'balanced' | 'grid_friendly'
  request_time: string
  top3: CandidateRecommendation[]
}

export const recommendationFixture: RecommendationFixture = {
  mode: 'balanced',
  request_time: '14:00',
  top3: [
    {
      rank: 1,
      station_id: 'S1',
      station_name: 'Market Road Hub',
      hour: 14,
      starts_in_h: 0,
      available_bays: 4,
      total_bays: 8,
      charger_kw: 7.4,
      wait_min: 0.0,
      detour_min: 0.0,
      grid_load_pct: 52.0,
      score: 0.128,
      score_breakdown: {
        wait_component: 0.000,
        detour_component: 0.000,
        imbalance_component: 0.042,
        risk_component: 0.086,
        weights: { wait: 0.25, detour: 0.25, balance: 0.25, risk: 0.25 },
      },
      why_reason:
        'Market Road has 4 vacant bays, 0 minutes of detour from your corridor, and zero Erlang-C queue delay. Loading remains safely below the 80% warning limit at 52.0%.',
    },
    {
      rank: 2,
      station_id: 'S2',
      station_name: 'Station Plaza',
      hour: 14,
      starts_in_h: 0,
      available_bays: 2,
      total_bays: 6,
      charger_kw: 7.4,
      wait_min: 4.2,
      detour_min: 4.0,
      grid_load_pct: 56.4,
      score: 0.285,
      score_breakdown: {
        wait_component: 0.070,
        detour_component: 0.067,
        imbalance_component: 0.055,
        risk_component: 0.093,
        weights: { wait: 0.25, detour: 0.25, balance: 0.25, risk: 0.25 },
      },
      why_reason:
        'Station Plaza provides 2 available bays with a minor 4-minute detour and ~4 minutes expected queuing time. Grid loading is well within safe thresholds.',
    },
    {
      rank: 3,
      station_id: 'S3',
      station_name: 'College Gate',
      hour: 15,
      starts_in_h: 1,
      available_bays: 1,
      total_bays: 6,
      charger_kw: 7.4,
      wait_min: 8.5,
      detour_min: 7.0,
      grid_load_pct: 68.2,
      score: 0.442,
      score_breakdown: {
        wait_component: 0.142,
        detour_component: 0.117,
        imbalance_component: 0.070,
        risk_component: 0.113,
        weights: { wait: 0.25, detour: 0.25, balance: 0.25, risk: 0.25 },
      },
      why_reason:
        'College Gate is operating near capacity (5/6 bays full). Waiting 1 hour for the 15:00 slot reduces queue time and relieves evening peak congestion.',
    },
  ],
}
