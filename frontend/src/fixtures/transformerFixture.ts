export interface TransformerFixture {
  transformer_id: string
  name: string
  rating_kva: number
  power_factor: number
  current_active_kw: number
  current_apparent_kva: number
  loading_percent: number
  ambient_temp_c: number
  derating_factor: number
  effective_kva: number
  warn_threshold_pct: number
  crit_threshold_pct: number
  risk_status: 'normal' | 'warn' | 'crit'
  peak_forecast_hour: number
  peak_forecast_p90_pct: number
  pandapower: {
    converged: boolean
    max_voltage_drop_pct: number
    transformer_losses_kw: number
    statutory_vdrop_limit_pct: number
  }
}

export const transformerFixture: TransformerFixture = {
  transformer_id: 'T1',
  name: 'TX-Metro-100kVA',
  rating_kva: 100.0,
  power_factor: 0.95,
  current_active_kw: 74.2,
  current_apparent_kva: 78.1,
  loading_percent: 78.1,
  ambient_temp_c: 32.5,
  derating_factor: 0.982,
  effective_kva: 98.2,
  warn_threshold_pct: 80.0,
  crit_threshold_pct: 90.0,
  risk_status: 'normal',
  peak_forecast_hour: 18,
  peak_forecast_p90_pct: 89.6,
  pandapower: {
    converged: true,
    max_voltage_drop_pct: 3.49,
    transformer_losses_kw: 2.14,
    statutory_vdrop_limit_pct: 5.0,
  },
}
