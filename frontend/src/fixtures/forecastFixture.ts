export interface ForecastFixture {
  hours: number[]
  p10: number[]
  p50: number[]
  p90: number[]
  warn_limit_pct: number
  crit_limit_pct: number
  model_version: string
  peak_p90_pct: number
  peak_hour: number
  first_warn_hour: number | null
  tod_slots: Array<{
    start_hour: number
    end_hour: number
    name: string
    rate_inr: number
    multiplier: number
  }>
}

export const forecastFixture: ForecastFixture = {
  hours: [14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
  p10: [48.2, 52.1, 58.4, 62.0, 68.5, 65.2, 54.0, 42.1, 32.5, 25.0, 18.2, 16.5, 15.0, 14.8, 15.2, 16.0, 22.4, 34.0, 45.2, 52.0, 48.0, 45.5, 46.0, 47.1],
  p50: [60.5, 66.8, 72.4, 78.5, 82.0, 79.2, 68.4, 55.0, 44.0, 36.2, 28.5, 24.0, 22.1, 21.5, 22.0, 24.5, 32.0, 48.0, 62.5, 68.0, 63.5, 59.0, 58.5, 59.8],
  p90: [74.2, 80.5, 84.8, 88.2, 89.6, 86.4, 76.8, 64.2, 52.0, 44.5, 36.0, 31.2, 28.5, 28.0, 29.2, 32.0, 42.5, 61.2, 75.8, 81.5, 76.2, 71.0, 72.5, 73.0],
  warn_limit_pct: 80.0,
  crit_limit_pct: 90.0,
  model_version: 'lightgbm_quantile_conformal_v1',
  peak_p90_pct: 89.6,
  peak_hour: 18,
  first_warn_hour: 15,
  tod_slots: [
    { start_hour: 9, end_hour: 17, name: 'Solar Off-Peak', rate_inr: 5.5, multiplier: 0.85 },
    { start_hour: 17, end_hour: 23, name: 'Evening Peak', rate_inr: 8.5, multiplier: 1.25 },
    { start_hour: 23, end_hour: 6, name: 'Night Off-Peak', rate_inr: 5.0, multiplier: 0.85 },
    { start_hour: 6, end_hour: 9, name: 'Morning Normal', rate_inr: 6.5, multiplier: 1.0 },
  ],
}
