/**
 * Tests for Zod form schemas — validates acceptance criteria:
 * "invalid input is blocked with a clear message"
 *
 * Run: cd frontend && npm test
 */
import { describe, it, expect } from 'vitest'
import {
  driverRequestSchema,
  DRIVER_REQUEST_DEFAULTS,
  operatorSettingsSchema,
  OPERATOR_SETTINGS_DEFAULTS,
  loginSchema,
} from '@/features/forms/schemas'

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------
function parseErrors(schema: { safeParse: (d: unknown) => { success: boolean; error?: { issues: Array<{ path: string[]; message: string }> } } }, data: unknown) {
  const result = schema.safeParse(data)
  if (result.success) return {}
  return Object.fromEntries(
    (result.error?.issues ?? []).map((i) => [i.path.join('.'), i.message]),
  )
}

// ---------------------------------------------------------------------------
// DriverRequestForm schema
// ---------------------------------------------------------------------------
describe('driverRequestSchema', () => {
  it('accepts valid defaults', () => {
    const result = driverRequestSchema.safeParse(DRIVER_REQUEST_DEFAULTS)
    expect(result.success).toBe(true)
  })

  it('rejects battery_pct below 5', () => {
    const errs = parseErrors(driverRequestSchema, { ...DRIVER_REQUEST_DEFAULTS, battery_pct: 3 })
    expect(errs['battery_pct']).toMatch(/at least 5/)
  })

  it('rejects battery_pct above 95', () => {
    const errs = parseErrors(driverRequestSchema, { ...DRIVER_REQUEST_DEFAULTS, battery_pct: 97 })
    expect(errs['battery_pct']).toMatch(/cannot exceed 95/)
  })

  it('rejects target_pct below 20', () => {
    // battery_pct=5 ensures target=15 passes cross-field (15>5) but fails .min(20)
    const errs = parseErrors(driverRequestSchema, { ...DRIVER_REQUEST_DEFAULTS, battery_pct: 5, target_pct: 15 })
    expect(errs['target_pct']).toMatch(/at least 20/)
  })

  it('rejects target_pct not exceeding battery_pct (cross-field)', () => {
    const errs = parseErrors(driverRequestSchema, {
      ...DRIVER_REQUEST_DEFAULTS,
      battery_pct: 70,
      target_pct: 70,
    })
    expect(errs['target_pct']).toMatch(/higher than current battery/)
  })

  it('rejects target_pct below battery_pct (cross-field)', () => {
    const errs = parseErrors(driverRequestSchema, {
      ...DRIVER_REQUEST_DEFAULTS,
      battery_pct: 80,
      target_pct: 60,
    })
    expect(errs['target_pct']).toMatch(/higher than current battery/)
  })

  it('rejects invalid connector_type', () => {
    const errs = parseErrors(driverRequestSchema, {
      ...DRIVER_REQUEST_DEFAULTS,
      connector_type: 'NACS',
    })
    // Zod enum produces "Invalid option: expected one of ..." or custom errorMap message
    expect(errs['connector_type']).toBeTruthy()
  })

  it('rejects departure_window_h below 0.5', () => {
    const errs = parseErrors(driverRequestSchema, {
      ...DRIVER_REQUEST_DEFAULTS,
      departure_window_h: 0.2,
    })
    expect(errs['departure_window_h']).toMatch(/at least 30 minutes/)
  })

  it('rejects departure_window_h above 12', () => {
    const errs = parseErrors(driverRequestSchema, {
      ...DRIVER_REQUEST_DEFAULTS,
      departure_window_h: 15,
    })
    expect(errs['departure_window_h']).toMatch(/cannot exceed 12/)
  })

  it('rejects invalid priority_mode', () => {
    const errs = parseErrors(driverRequestSchema, {
      ...DRIVER_REQUEST_DEFAULTS,
      priority_mode: 'turbo',
    })
    // Zod enum produces "Invalid option: expected one of ..." or custom errorMap message
    expect(errs['priority_mode']).toBeTruthy()
  })

  it('accepts maximum valid values', () => {
    const result = driverRequestSchema.safeParse({
      battery_pct: 10,
      target_pct: 100,
      connector_type: 'CCS',
      departure_window_h: 12,
      priority_mode: 'grid_friendly',
    })
    expect(result.success).toBe(true)
  })
})

// ---------------------------------------------------------------------------
// OperatorSettingsForm schema
// ---------------------------------------------------------------------------
describe('operatorSettingsSchema', () => {
  it('accepts valid defaults', () => {
    const result = operatorSettingsSchema.safeParse(OPERATOR_SETTINGS_DEFAULTS)
    expect(result.success).toBe(true)
  })

  it('rejects transformer_kva below 10', () => {
    const errs = parseErrors(operatorSettingsSchema, { ...OPERATOR_SETTINGS_DEFAULTS, transformer_kva: 5 })
    expect(errs['transformer_kva']).toMatch(/at least 10 kVA/)
  })

  it('rejects transformer_kva above 2000', () => {
    const errs = parseErrors(operatorSettingsSchema, { ...OPERATOR_SETTINGS_DEFAULTS, transformer_kva: 3000 })
    expect(errs['transformer_kva']).toMatch(/cannot exceed 2000/)
  })

  it('rejects warn_threshold_pct below 50', () => {
    const errs = parseErrors(operatorSettingsSchema, { ...OPERATOR_SETTINGS_DEFAULTS, warn_threshold_pct: 40 })
    expect(errs['warn_threshold_pct']).toMatch(/at least 50/)
  })

  it('rejects crit_threshold_pct not exceeding warn (cross-field)', () => {
    const errs = parseErrors(operatorSettingsSchema, {
      ...OPERATOR_SETTINGS_DEFAULTS,
      warn_threshold_pct: 85,
      crit_threshold_pct: 85,
    })
    expect(errs['crit_threshold_pct']).toMatch(/higher than warning/)
  })

  it('rejects weights that do not sum to 1.0', () => {
    const errs = parseErrors(operatorSettingsSchema, {
      ...OPERATOR_SETTINGS_DEFAULTS,
      weight_queue: 0.6,
      weight_distance: 0.3,
      weight_grid: 0.3,  // sum = 1.2
    })
    expect(errs['weight_grid']).toMatch(/sum to 1.0/)
  })

  it('accepts weights summing to 1.0 within float tolerance', () => {
    const result = operatorSettingsSchema.safeParse({
      ...OPERATOR_SETTINGS_DEFAULTS,
      weight_queue: 0.5,
      weight_distance: 0.3,
      weight_grid: 0.2,
    })
    expect(result.success).toBe(true)
  })

  it('rejects individual weight above 1', () => {
    const errs = parseErrors(operatorSettingsSchema, {
      ...OPERATOR_SETTINGS_DEFAULTS,
      weight_queue: 1.5,
    })
    expect(errs['weight_queue']).toMatch(/cannot exceed 1/)
  })
})

// ---------------------------------------------------------------------------
// Login schema
// ---------------------------------------------------------------------------
describe('loginSchema', () => {
  it('accepts valid credentials', () => {
    const result = loginSchema.safeParse({ username: 'operator_c1', password: 'secret' })
    expect(result.success).toBe(true)
  })

  it('rejects username shorter than 3 chars', () => {
    const errs = parseErrors(loginSchema, { username: 'ab', password: 'secret' })
    expect(errs['username']).toMatch(/at least 3/)
  })

  it('rejects username with invalid characters', () => {
    const errs = parseErrors(loginSchema, { username: 'user name!', password: 'secret' })
    expect(errs['username']).toMatch(/letters, numbers/)
  })

  it('rejects empty password', () => {
    const errs = parseErrors(loginSchema, { username: 'operator', password: '' })
    expect(errs['password']).toMatch(/at least 4/)
  })

  it('rejects password shorter than 4 chars', () => {
    const errs = parseErrors(loginSchema, { username: 'operator', password: 'ab' })
    expect(errs['password']).toMatch(/at least 4/)
  })

  it('accepts all valid connector and mode combinations', () => {
    for (const connector of ['Type 2', 'CCS', 'CHAdeMO', 'GB/T'] as const) {
      for (const mode of ['fastest', 'balanced', 'grid_friendly'] as const) {
        const result = driverRequestSchema.safeParse({
          ...DRIVER_REQUEST_DEFAULTS,
          connector_type: connector,
          priority_mode: mode,
        })
        expect(result.success, `${connector}/${mode} should be valid`).toBe(true)
      }
    }
  })
})
