export interface ReplayStateFixture {
  is_playing: boolean
  speed_multiplier: 1 | 10 | 60
  current_step_hours: number
  total_horizon_hours: number
  start_timestamp: string
  current_timestamp: string
  clock_time_display: string
  metrics: {
    fcfs: {
      peak_load_kw: number
      overload_warn_hours: number
      overload_crit_hours: number
      mean_wait_min: number
      jain_fairness: number
    }
    smart: {
      peak_load_kw: number
      overload_warn_hours: number
      overload_crit_hours: number
      mean_wait_min: number
      jain_fairness: number
    }
    improvement: {
      peak_shaving_kw: number
      peak_shaving_pct: number
      wait_reduction_pct: number
      overload_eliminated_pct: number
    }
  }
}

export const replayFixture: ReplayStateFixture = {
  is_playing: false,
  speed_multiplier: 60,
  current_step_hours: 42,
  total_horizon_hours: 168,
  start_timestamp: '2026-10-01T00:00:00Z',
  current_timestamp: '2026-10-02T18:00:00Z',
  clock_time_display: 'Day 3, 18:00 UTC (Evening Peak)',
  metrics: {
    fcfs: {
      peak_load_kw: 88.5,
      overload_warn_hours: 3.4,
      overload_crit_hours: 1.2,
      mean_wait_min: 18.6,
      jain_fairness: 0.81,
    },
    smart: {
      peak_load_kw: 74.2,
      overload_warn_hours: 0.4,
      overload_crit_hours: 0.0,
      mean_wait_min: 8.1,
      jain_fairness: 0.94,
    },
    improvement: {
      peak_shaving_kw: 14.3,
      peak_shaving_pct: 16.2,
      wait_reduction_pct: 56.5,
      overload_eliminated_pct: 100.0,
    },
  },
}
