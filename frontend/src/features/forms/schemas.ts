/**
 * Shared Zod schemas for all three forms.
 * These are the single source of truth — the backend Pydantic models
 * must enforce the same limits (see backend/app/api/v1/schemas.py).
 */
import { z } from 'zod'

// ---------------------------------------------------------------------------
// Connector types
// ---------------------------------------------------------------------------
export const CONNECTOR_TYPES = ['Type 2', 'CCS', 'CHAdeMO', 'GB/T'] as const
export type ConnectorType = (typeof CONNECTOR_TYPES)[number]

// ---------------------------------------------------------------------------
// Priority modes
// ---------------------------------------------------------------------------
export const PRIORITY_MODES = ['fastest', 'balanced', 'grid_friendly'] as const
export type PriorityMode = (typeof PRIORITY_MODES)[number]

// ---------------------------------------------------------------------------
// Driver Request Form
// ---------------------------------------------------------------------------
export const driverRequestSchema = z
  .object({
    battery_pct: z
      .number({ invalid_type_error: 'Enter a number between 5 and 95' })
      .min(5, 'Current battery must be at least 5 % — plug in before it runs lower')
      .max(95, 'Current battery cannot exceed 95 %'),

    target_pct: z
      .number({ invalid_type_error: 'Enter a number between 20 and 100' })
      .min(20, 'Target must be at least 20 % — choose a meaningful charge level')
      .max(100, 'Target cannot exceed 100 %'),

    connector_type: z.enum(CONNECTOR_TYPES, {
      errorMap: () => ({ message: 'Select a connector type from the list' }),
    }),

    departure_window_h: z
      .number({ invalid_type_error: 'Enter a number between 0.5 and 12' })
      .min(0.5, 'Departure window must be at least 30 minutes (0.5 h)')
      .max(12, 'Departure window cannot exceed 12 hours — use overnight scheduling instead'),

    priority_mode: z.enum(PRIORITY_MODES, {
      errorMap: () => ({ message: 'Select a priority mode' }),
    }),
  })
  .refine((d) => d.target_pct > d.battery_pct, {
    message: 'Target % must be higher than current battery %',
    path: ['target_pct'],
  })

export type DriverRequestValues = z.infer<typeof driverRequestSchema>

export const DRIVER_REQUEST_DEFAULTS: DriverRequestValues = {
  battery_pct: 20,
  target_pct: 80,
  connector_type: 'Type 2',
  departure_window_h: 2,
  priority_mode: 'balanced',
}

// ---------------------------------------------------------------------------
// Operator Settings Form
// ---------------------------------------------------------------------------
export const operatorSettingsSchema = z
  .object({
    transformer_kva: z
      .number({ invalid_type_error: 'Enter kVA between 10 and 2000' })
      .min(10, 'Transformer must be rated at least 10 kVA')
      .max(2000, 'Transformer rating cannot exceed 2000 kVA in this system'),

    warn_threshold_pct: z
      .number({ invalid_type_error: 'Enter a percentage between 50 and 98' })
      .min(50, 'Warning threshold must be at least 50 %')
      .max(98, 'Warning threshold cannot exceed 98 %'),

    crit_threshold_pct: z
      .number({ invalid_type_error: 'Enter a percentage between 51 and 99' })
      .min(51, 'Critical threshold must be at least 51 %')
      .max(99, 'Critical threshold cannot exceed 99 %'),

    weight_queue: z
      .number({ invalid_type_error: 'Enter a weight between 0 and 1' })
      .min(0, 'Weight cannot be negative')
      .max(1, 'Weight cannot exceed 1.0'),

    weight_distance: z
      .number({ invalid_type_error: 'Enter a weight between 0 and 1' })
      .min(0, 'Weight cannot be negative')
      .max(1, 'Weight cannot exceed 1.0'),

    weight_grid: z
      .number({ invalid_type_error: 'Enter a weight between 0 and 1' })
      .min(0, 'Weight cannot be negative')
      .max(1, 'Weight cannot exceed 1.0'),
  })
  .refine((d) => d.crit_threshold_pct > d.warn_threshold_pct, {
    message: 'Critical threshold must be higher than warning threshold',
    path: ['crit_threshold_pct'],
  })
  .refine(
    (d) => {
      const sum = d.weight_queue + d.weight_distance + d.weight_grid
      return sum >= 0.99 && sum <= 1.01
    },
    {
      message: 'Recommendation weights must sum to 1.0 — adjust the sliders so they total exactly 100 %',
      path: ['weight_grid'],
    },
  )

export type OperatorSettingsValues = z.infer<typeof operatorSettingsSchema>

export const OPERATOR_SETTINGS_DEFAULTS: OperatorSettingsValues = {
  transformer_kva: 100,
  warn_threshold_pct: 80,
  crit_threshold_pct: 90,
  weight_queue: 0.5,
  weight_distance: 0.3,
  weight_grid: 0.2,
}

// ---------------------------------------------------------------------------
// Login Form
// ---------------------------------------------------------------------------
export const loginSchema = z.object({
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(64, 'Username cannot exceed 64 characters')
    .regex(/^[a-zA-Z0-9_.-]+$/, 'Username can only contain letters, numbers, underscores, dots, or hyphens'),

  password: z
    .string()
    .min(4, 'Password must be at least 4 characters')
    .max(128, 'Password cannot exceed 128 characters'),
})

export type LoginValues = z.infer<typeof loginSchema>

export const LOGIN_DEFAULTS: LoginValues = {
  username: '',
  password: '',
}
