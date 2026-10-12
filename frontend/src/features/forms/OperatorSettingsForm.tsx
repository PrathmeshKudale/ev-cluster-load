/**
 * OperatorSettingsForm — React Hook Form + Zod
 *
 * Fields:
 *   - transformer_kva        (10–2000)
 *   - warn_threshold_pct     (50–98, < crit)
 *   - crit_threshold_pct     (51–99, > warn)
 *   - weight_queue           (0–1, sum must = 1)
 *   - weight_distance        (0–1, sum must = 1)
 *   - weight_grid            (0–1, sum must = 1)
 *
 * Cross-field rules: crit > warn; weights sum to 1.
 * Inline errors tell operators exactly what to change.
 */
import React from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  operatorSettingsSchema,
  OperatorSettingsValues,
  OPERATOR_SETTINGS_DEFAULTS,
} from './schemas'
import {
  FieldWrapper,
  NumberInput,
  RangeInput,
  FormSection,
  SubmitButton,
} from './FormFields'

interface OperatorSettingsFormProps {
  onSubmit: (values: OperatorSettingsValues) => void | Promise<void>
  isSubmitting?: boolean
  defaultValues?: Partial<OperatorSettingsValues>
}

export const OperatorSettingsForm: React.FC<OperatorSettingsFormProps> = ({
  onSubmit,
  isSubmitting,
  defaultValues,
}) => {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<OperatorSettingsValues>({
    resolver: zodResolver(operatorSettingsSchema),
    defaultValues: { ...OPERATOR_SETTINGS_DEFAULTS, ...defaultValues },
    mode: 'onBlur',
  })

  const wq = watch('weight_queue')
  const wd = watch('weight_distance')
  const wg = watch('weight_grid')
  const weightSum = Math.round((wq + wd + wg) * 100) / 100

  const warnPct = watch('warn_threshold_pct')
  const critPct = watch('crit_threshold_pct')

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Operator cluster settings"
      style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
    >
      {/* ---- Transformer ---- */}
      <FormSection title="Transformer">
        <FieldWrapper
          id="transformer_kva"
          label="Transformer rating"
          hint="Nameplate capacity in kVA (10–2000)"
          error={errors.transformer_kva}
          required
        >
          <NumberInput
            {...register('transformer_kva', { valueAsNumber: true })}
            error={errors.transformer_kva}
            min={10}
            max={2000}
            step={5}
            placeholder="e.g. 100"
          />
        </FieldWrapper>
      </FormSection>

      {/* ---- Thresholds ---- */}
      <FormSection title="Alert Thresholds">
        <FieldWrapper
          id="warn_threshold_pct"
          label="Warning threshold"
          hint="Amber alert fires when load reaches this % of transformer rating"
          error={errors.warn_threshold_pct}
          required
        >
          <RangeInput
            {...register('warn_threshold_pct', { valueAsNumber: true })}
            error={errors.warn_threshold_pct}
            min={50}
            max={98}
            step={1}
            valueLabel={`${warnPct} %`}
            onChange={(e) => setValue('warn_threshold_pct', Number(e.target.value), { shouldValidate: true })}
          />
        </FieldWrapper>

        <FieldWrapper
          id="crit_threshold_pct"
          label="Critical threshold"
          hint={`Red alert fires at this %. Must be above warning threshold (${warnPct} %).`}
          error={errors.crit_threshold_pct}
          required
        >
          <RangeInput
            {...register('crit_threshold_pct', { valueAsNumber: true })}
            error={errors.crit_threshold_pct}
            min={51}
            max={99}
            step={1}
            valueLabel={`${critPct} %`}
            onChange={(e) => setValue('crit_threshold_pct', Number(e.target.value), { shouldValidate: true })}
          />
        </FieldWrapper>

        {/* Threshold visualiser */}
        <div
          aria-label="Threshold band preview"
          style={{ position: 'relative', height: '12px', borderRadius: '6px', background: 'var(--color-ink-700)' }}
        >
          <div
            style={{
              position: 'absolute',
              left: `${warnPct}%`,
              width: `${critPct - warnPct}%`,
              height: '100%',
              background: 'var(--color-warn-amber, #f59e0b)',
              borderRadius: '3px',
              opacity: 0.8,
            }}
          />
          <div
            style={{
              position: 'absolute',
              left: `${critPct}%`,
              right: 0,
              height: '100%',
              background: 'var(--color-crit-red, #ef4444)',
              borderRadius: '0 6px 6px 0',
              opacity: 0.8,
            }}
          />
        </div>
        <p style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '-4px' }}>
          Green 0–{warnPct} % · Amber {warnPct}–{critPct} % · Red {critPct}–100 %
        </p>
      </FormSection>

      {/* ---- Recommendation weights ---- */}
      <FormSection title="Recommendation Weights">
        <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', margin: 0 }}>
          Adjust how the smart dispatch policy scores each station. Weights must sum to{' '}
          <strong style={{ color: weightSum === 1 ? 'var(--color-trafo-blue)' : 'var(--color-crit-red, #ef4444)' }}>
            {weightSum.toFixed(2)}
          </strong>{' '}
          / 1.00
        </p>

        <FieldWrapper
          id="weight_queue"
          label="Queue pressure weight"
          hint="Preference for stations with shorter queues"
          error={errors.weight_queue}
          required
        >
          <RangeInput
            {...register('weight_queue', { valueAsNumber: true })}
            error={errors.weight_queue}
            min={0}
            max={1}
            step={0.05}
            valueLabel={wq.toFixed(2)}
            onChange={(e) => setValue('weight_queue', Number(e.target.value), { shouldValidate: true })}
          />
        </FieldWrapper>

        <FieldWrapper
          id="weight_distance"
          label="Distance weight"
          hint="Preference for closer stations"
          error={errors.weight_distance}
          required
        >
          <RangeInput
            {...register('weight_distance', { valueAsNumber: true })}
            error={errors.weight_distance}
            min={0}
            max={1}
            step={0.05}
            valueLabel={wd.toFixed(2)}
            onChange={(e) => setValue('weight_distance', Number(e.target.value), { shouldValidate: true })}
          />
        </FieldWrapper>

        <FieldWrapper
          id="weight_grid"
          label="Grid load weight"
          hint="Preference for stations with lower transformer load — helps prevent overload"
          error={errors.weight_grid}
          required
        >
          <RangeInput
            {...register('weight_grid', { valueAsNumber: true })}
            error={errors.weight_grid}
            min={0}
            max={1}
            step={0.05}
            valueLabel={wg.toFixed(2)}
            onChange={(e) => setValue('weight_grid', Number(e.target.value), { shouldValidate: true })}
          />
        </FieldWrapper>
      </FormSection>

      <SubmitButton
        loading={isSubmitting}
        label="Save Settings"
        loadingLabel="Saving…"
      />
    </form>
  )
}
