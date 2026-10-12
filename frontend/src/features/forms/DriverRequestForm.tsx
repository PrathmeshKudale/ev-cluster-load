/**
 * DriverRequestForm — React Hook Form + Zod
 *
 * Fields: battery_pct, target_pct, connector_type, departure_window_h, priority_mode
 * Inline errors tell users exactly how to fix the problem.
 * Safe defaults: 20 % → 80 %, Type 2, 2 h window, balanced mode.
 */
import React from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  driverRequestSchema,
  DriverRequestValues,
  DRIVER_REQUEST_DEFAULTS,
  CONNECTOR_TYPES,
  PRIORITY_MODES,
} from './schemas'
import {
  FieldWrapper,
  NumberInput,
  SelectInput,
  FormSection,
  SubmitButton,
} from './FormFields'

interface DriverRequestFormProps {
  onSubmit: (values: DriverRequestValues) => void | Promise<void>
  isSubmitting?: boolean
  defaultValues?: Partial<DriverRequestValues>
}

const PRIORITY_LABELS: Record<string, string> = {
  fastest: 'Fastest — get the nearest free charger immediately',
  balanced: 'Balanced — mix of speed, cost, and grid load',
  grid_friendly: 'Grid-friendly — prefer off-peak hours to help the grid',
}

export const DriverRequestForm: React.FC<DriverRequestFormProps> = ({
  onSubmit,
  isSubmitting,
  defaultValues,
}) => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<DriverRequestValues>({
    resolver: zodResolver(driverRequestSchema),
    defaultValues: { ...DRIVER_REQUEST_DEFAULTS, ...defaultValues },
    mode: 'onBlur',
  })

  const batteryPct = watch('battery_pct')
  const targetPct = watch('target_pct')

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Driver charging request"
      style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
    >
      <FormSection title="Battery State">
        <FieldWrapper
          id="battery_pct"
          label="Current battery"
          hint="How charged is your battery right now? (5–95 %)"
          error={errors.battery_pct}
          required
        >
          <NumberInput
            {...register('battery_pct', { valueAsNumber: true })}
            error={errors.battery_pct}
            min={5}
            max={95}
            step={1}
            placeholder="e.g. 20"
          />
        </FieldWrapper>

        <FieldWrapper
          id="target_pct"
          label="Target charge"
          hint={`Charge to this level before your departure. Must be above current ${batteryPct ?? 0} %.`}
          error={errors.target_pct}
          required
        >
          <NumberInput
            {...register('target_pct', { valueAsNumber: true })}
            error={errors.target_pct}
            min={20}
            max={100}
            step={1}
            placeholder="e.g. 80"
          />
        </FieldWrapper>

        {/* Live indicator */}
        {!errors.battery_pct && !errors.target_pct && batteryPct && targetPct && (
          <p
            style={{
              fontSize: '13px',
              color: 'var(--color-ink-300)',
              fontStyle: 'italic',
            }}
            aria-live="polite"
          >
            Charging {targetPct - batteryPct} % — estimated{' '}
            {Math.ceil(((targetPct - batteryPct) / 100) * 40)} kWh at 7.4 kW/charger
          </p>
        )}
      </FormSection>

      <FormSection title="Charger & Schedule">
        <FieldWrapper
          id="connector_type"
          label="Connector type"
          hint="Must match your vehicle's inlet"
          error={errors.connector_type}
          required
        >
          <SelectInput
            {...register('connector_type')}
            error={errors.connector_type}
            options={CONNECTOR_TYPES}
          />
        </FieldWrapper>

        <FieldWrapper
          id="departure_window_h"
          label="Departure window"
          hint="How many hours until you need to leave? (0.5–12 h)"
          error={errors.departure_window_h}
          required
        >
          <NumberInput
            {...register('departure_window_h', { valueAsNumber: true })}
            error={errors.departure_window_h}
            min={0.5}
            max={12}
            step={0.5}
            placeholder="e.g. 2"
          />
        </FieldWrapper>
      </FormSection>

      <FormSection title="Priority Mode">
        <FieldWrapper
          id="priority_mode"
          label="How should we pick your station?"
          error={errors.priority_mode}
          required
        >
          <SelectInput
            {...register('priority_mode')}
            error={errors.priority_mode}
            options={PRIORITY_MODES}
          />
        </FieldWrapper>

        {/* Descriptive hint below select */}
        {watch('priority_mode') && (
          <p
            style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '-8px' }}
            aria-live="polite"
          >
            {PRIORITY_LABELS[watch('priority_mode')]}
          </p>
        )}
      </FormSection>

      <SubmitButton
        loading={isSubmitting}
        label="Find My Station →"
        loadingLabel="Finding best station…"
      />
    </form>
  )
}
