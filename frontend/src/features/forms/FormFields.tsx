/**
 * Shared accessible form field primitives.
 * Every input renders: label → input → inline error message.
 * Focus rings, aria-invalid, aria-describedby wired for WCAG AA.
 */
import React from 'react'
import { FieldError } from 'react-hook-form'
import { AlertCircle } from 'lucide-react'

// ---------------------------------------------------------------------------
// Utility: CSS-in-JS token shortcuts
// ---------------------------------------------------------------------------
const tokens = {
  inkBorder: 'var(--color-ink-600)',
  errorRed: 'var(--color-crit-red, #ef4444)',
  ink100: 'var(--color-ink-100)',
  ink300: 'var(--color-ink-300)',
  ink700: 'var(--color-ink-700)',
  ink800: 'var(--color-ink-800)',
  trafoBlue: 'var(--color-trafo-blue)',
  fontSans: 'var(--font-sans, "Atkinson Hyperlegible", sans-serif)',
  radiusMd: 'var(--radius-md, 6px)',
}

// ---------------------------------------------------------------------------
// FieldWrapper: label + children + optional error
// ---------------------------------------------------------------------------
interface FieldWrapperProps {
  id: string
  label: string
  hint?: string
  error?: FieldError
  required?: boolean
  children: React.ReactNode
}

export const FieldWrapper: React.FC<FieldWrapperProps> = ({
  id,
  label,
  hint,
  error,
  required,
  children,
}) => {
  const errorId = `${id}-error`
  const hintId = `${id}-hint`

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      <label
        htmlFor={id}
        style={{
          fontFamily: tokens.fontSans,
          fontSize: '14px',
          fontWeight: 600,
          color: tokens.ink300,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
        }}
      >
        {label}
        {required && (
          <span style={{ color: tokens.errorRed }} aria-label="required">
            *
          </span>
        )}
      </label>

      {hint && (
        <span
          id={hintId}
          style={{ fontSize: '12px', color: tokens.ink300, marginTop: '-2px' }}
        >
          {hint}
        </span>
      )}

      {/* Inject aria props via cloneElement */}
      {React.isValidElement(children)
        ? React.cloneElement(children as React.ReactElement<React.HTMLAttributes<HTMLElement>>, {
            id,
            'aria-invalid': error ? true : undefined,
            'aria-describedby':
              [error ? errorId : '', hint ? hintId : ''].filter(Boolean).join(' ') || undefined,
          })
        : children}

      {error && (
        <span
          id={errorId}
          role="alert"
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '5px',
            fontSize: '13px',
            color: tokens.errorRed,
            fontFamily: tokens.fontSans,
          }}
        >
          <AlertCircle size={14} style={{ flexShrink: 0, marginTop: '1px' }} />
          {error.message}
        </span>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Shared input base style
// ---------------------------------------------------------------------------
const inputBase = (hasError: boolean): React.CSSProperties => ({
  width: '100%',
  boxSizing: 'border-box',
  padding: '10px 12px',
  fontSize: '15px',
  fontFamily: tokens.fontSans,
  borderRadius: tokens.radiusMd,
  border: `1.5px solid ${hasError ? tokens.errorRed : tokens.inkBorder}`,
  background: tokens.ink800,
  color: tokens.ink100,
  outline: 'none',
  transition: 'border-color 0.15s, box-shadow 0.15s',
})

// ---------------------------------------------------------------------------
// TextInput
// ---------------------------------------------------------------------------
interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: FieldError
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  ({ error, style, ...props }, ref) => (
    <input
      ref={ref}
      style={{ ...inputBase(!!error), ...style }}
      onFocus={(e) => {
        e.currentTarget.style.boxShadow = `0 0 0 3px ${tokens.trafoBlue}40`
        e.currentTarget.style.borderColor = tokens.trafoBlue
      }}
      onBlur={(e) => {
        e.currentTarget.style.boxShadow = 'none'
        e.currentTarget.style.borderColor = error ? tokens.errorRed : tokens.inkBorder
      }}
      {...props}
    />
  ),
)
TextInput.displayName = 'TextInput'

// ---------------------------------------------------------------------------
// NumberInput (converts string → number for RHF valueAsNumber)
// ---------------------------------------------------------------------------
export const NumberInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  ({ error, ...props }, ref) => (
    <TextInput
      ref={ref}
      type="number"
      error={error}
      inputMode="decimal"
      {...props}
    />
  ),
)
NumberInput.displayName = 'NumberInput'

// ---------------------------------------------------------------------------
// SelectInput
// ---------------------------------------------------------------------------
interface SelectInputProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  error?: FieldError
  options: readonly string[]
}

export const SelectInput = React.forwardRef<HTMLSelectElement, SelectInputProps>(
  ({ error, options, style, ...props }, ref) => (
    <select
      ref={ref}
      style={{ ...inputBase(!!error), cursor: 'pointer', ...style }}
      onFocus={(e) => {
        e.currentTarget.style.boxShadow = `0 0 0 3px ${tokens.trafoBlue}40`
        e.currentTarget.style.borderColor = tokens.trafoBlue
      }}
      onBlur={(e) => {
        e.currentTarget.style.boxShadow = 'none'
        e.currentTarget.style.borderColor = error ? tokens.errorRed : tokens.inkBorder
      }}
      {...props}
    >
      {options.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  ),
)
SelectInput.displayName = 'SelectInput'

// ---------------------------------------------------------------------------
// RangeInput with value label
// ---------------------------------------------------------------------------
interface RangeInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: FieldError
  valueLabel?: string
}

export const RangeInput = React.forwardRef<HTMLInputElement, RangeInputProps>(
  ({ error, valueLabel, style, ...props }, ref) => (
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <input
        ref={ref}
        type="range"
        style={{
          flex: 1,
          accentColor: error ? tokens.errorRed : tokens.trafoBlue,
          cursor: 'pointer',
          ...style,
        }}
        {...props}
      />
      {valueLabel !== undefined && (
        <span
          style={{
            minWidth: '42px',
            textAlign: 'right',
            fontSize: '14px',
            fontWeight: 700,
            color: tokens.ink100,
            fontFamily: tokens.fontSans,
          }}
        >
          {valueLabel}
        </span>
      )}
    </div>
  ),
)
RangeInput.displayName = 'RangeInput'

// ---------------------------------------------------------------------------
// FormSection: card wrapper with title
// ---------------------------------------------------------------------------
interface FormSectionProps {
  title: string
  children: React.ReactNode
}

export const FormSection: React.FC<FormSectionProps> = ({ title, children }) => (
  <fieldset
    style={{
      border: `1px solid var(--color-ink-700, #333)`,
      borderRadius: 'var(--radius-lg, 10px)',
      padding: '20px',
      margin: 0,
    }}
  >
    <legend
      style={{
        padding: '0 8px',
        fontSize: '13px',
        fontWeight: 700,
        fontFamily: tokens.fontSans,
        color: tokens.ink300,
        textTransform: 'uppercase',
        letterSpacing: '0.06em',
      }}
    >
      {title}
    </legend>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>{children}</div>
  </fieldset>
)

// ---------------------------------------------------------------------------
// SubmitButton with loading state
// ---------------------------------------------------------------------------
interface SubmitButtonProps {
  loading?: boolean
  label: string
  loadingLabel?: string
}

export const SubmitButton: React.FC<SubmitButtonProps> = ({
  loading,
  label,
  loadingLabel = 'Submitting…',
}) => (
  <button
    type="submit"
    disabled={loading}
    style={{
      width: '100%',
      padding: '12px',
      fontSize: '15px',
      fontWeight: 700,
      fontFamily: tokens.fontSans,
      borderRadius: tokens.radiusMd,
      border: 'none',
      background: loading ? tokens.ink700 : tokens.trafoBlue,
      color: '#ffffff',
      cursor: loading ? 'not-allowed' : 'pointer',
      opacity: loading ? 0.7 : 1,
      transition: 'all 0.15s',
      minHeight: '48px',
    }}
    aria-busy={loading}
  >
    {loading ? loadingLabel : label}
  </button>
)
