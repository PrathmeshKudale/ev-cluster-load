/**
 * LoginForm component — RHF + Zod, replaces the manual useState validation.
 * Wires into useLoginMutation for API submission.
 */
import React, { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Eye, EyeOff } from 'lucide-react'
import { loginSchema, LoginValues, LOGIN_DEFAULTS } from './schemas'
import { FieldWrapper, TextInput, FormSection, SubmitButton } from './FormFields'

interface LoginFormProps {
  onSubmit: (values: LoginValues) => void | Promise<void>
  isSubmitting?: boolean
  serverError?: string
}

export const LoginForm: React.FC<LoginFormProps> = ({
  onSubmit,
  isSubmitting,
  serverError,
}) => {
  const [showPassword, setShowPassword] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: LOGIN_DEFAULTS,
    mode: 'onBlur',
  })

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      noValidate
      aria-label="Sign in"
      style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}
    >
      <FormSection title="Credentials">
        <FieldWrapper
          id="username"
          label="Username"
          hint="Letters, numbers, underscores, dots, or hyphens (min 3 characters)"
          error={errors.username}
          required
        >
          <TextInput
            {...register('username')}
            error={errors.username}
            type="text"
            autoComplete="username"
            placeholder="e.g. operator_c1"
            spellCheck={false}
          />
        </FieldWrapper>

        <FieldWrapper
          id="password"
          label="Password"
          error={errors.password}
          required
        >
          {/* Password with show/hide toggle */}
          <div style={{ position: 'relative' }}>
            <TextInput
              {...register('password')}
              error={errors.password}
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              placeholder="Enter your password"
              style={{ paddingRight: '44px' }}
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              style={{
                position: 'absolute',
                right: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                color: 'var(--color-ink-300)',
                display: 'inline-flex',
                padding: '4px',
              }}
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </FieldWrapper>
      </FormSection>

      {/* Server-side error (wrong credentials etc.) */}
      {serverError && (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239,68,68,0.12)',
            border: '1px solid var(--color-crit-red, #ef4444)',
            fontSize: '14px',
            color: 'var(--color-crit-red, #ef4444)',
          }}
        >
          {serverError}
        </div>
      )}

      <SubmitButton
        loading={isSubmitting}
        label="Sign in →"
        loadingLabel="Signing in…"
      />
    </form>
  )
}
