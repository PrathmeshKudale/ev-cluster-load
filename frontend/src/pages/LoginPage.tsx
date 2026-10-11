import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useLoginMutation } from '@/lib/queries'
import { useUIStore } from '@/store/uiStore'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Lock, User, AlertCircle, Loader2, ArrowRight } from 'lucide-react'

export const LoginPage: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const setAccessToken = useUIStore((s) => s.setAccessToken)
  const setUserRole = useUIStore((s) => s.setUserRole)
  const setUsername = useUIStore((s) => s.setUsername)
  const setPersona = useUIStore((s) => s.setPersona)
  const showToast = useUIStore((s) => s.showToast)

  const [usernameInput, setUsernameInput] = useState('')
  const [passwordInput, setPasswordInput] = useState('')
  const [errors, setErrors] = useState<{ username?: string; password?: string }>({})

  const loginMutation = useLoginMutation()

  const validate = () => {
    const errs: { username?: string; password?: string } = {}
    if (!usernameInput.trim()) {
      errs.username = 'Username is required'
    } else if (usernameInput.trim().length < 3) {
      errs.username = 'Username must be at least 3 characters'
    }

    if (!passwordInput) {
      errs.password = 'Password is required'
    } else if (passwordInput.length < 4) {
      errs.password = 'Password must be at least 4 characters'
    }

    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return

    try {
      const res = await loginMutation.mutateAsync({
        username: usernameInput.trim(),
        password: passwordInput,
      })

      const role = (res.user?.role ?? 'driver') as 'driver' | 'operator' | 'admin' | 'judge'
      setAccessToken(res.access_token)
      setUserRole(role)
      setUsername(usernameInput.trim())

      if (role === 'operator' || role === 'admin') {
        setPersona('operator')
      } else {
        setPersona('driver')
      }

      showToast(`Welcome, ${usernameInput.trim()}! Logged in as ${role}.`, 'success')

      const from = (location.state as { from?: { pathname: string } })?.from?.pathname
      if (from) {
        navigate(from, { replace: true })
      } else {
        navigate(role === 'operator' || role === 'admin' ? '/operator' : '/driver', { replace: true })
      }
    } catch (err: unknown) {
      // Toast is already shown by apiFetch, but we can set form error
      setErrors({ password: (err as Error).message ?? 'Invalid credentials' })
    }
  }

  const handleQuickLogin = (user: string, pass: string) => {
    setUsernameInput(user)
    setPasswordInput(pass)
    setErrors({})
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '32px 16px',
      }}
    >
      <div style={{ width: '100%', maxWidth: '420px' }}>
        <Card>
          <CardHeader>
            <div style={{ textAlign: 'center', marginBottom: '8px' }}>
              <div
                style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '10px',
                  background: 'var(--color-trafo-blue)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  marginBottom: '12px',
                }}
              >
                <Lock size={24} />
              </div>
              <CardTitle style={{ fontSize: '20px' }}>Sign In to GridFlow EV</CardTitle>
              <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '4px' }}>
                JWT authentication with Argon2 password verification
              </p>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Username */}
              <div>
                <label
                  htmlFor="login-username"
                  style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px', color: 'var(--color-ink-200)' }}
                >
                  Username
                </label>
                <div style={{ position: 'relative' }}>
                  <User
                    size={16}
                    color="var(--color-ink-400)"
                    style={{ position: 'absolute', left: '12px', top: '12px' }}
                  />
                  <input
                    id="login-username"
                    type="text"
                    value={usernameInput}
                    onChange={(e) => setUsernameInput(e.target.value)}
                    placeholder="e.g. operator or driver"
                    style={{
                      width: '100%',
                      padding: '10px 12px 10px 38px',
                      borderRadius: '6px',
                      background: 'var(--color-ink-900)',
                      border: errors.username ? '1px solid var(--color-crit-red)' : '1px solid var(--color-ink-700)',
                      color: '#fff',
                      fontSize: '14px',
                      fontFamily: 'var(--font-sans)',
                      outline: 'none',
                    }}
                  />
                </div>
                {errors.username && (
                  <p style={{ fontSize: '12px', color: 'var(--color-crit-red)', margin: '4px 0 0', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <AlertCircle size={12} /> {errors.username}
                  </p>
                )}
              </div>

              {/* Password */}
              <div>
                <label
                  htmlFor="login-password"
                  style={{ display: 'block', fontSize: '13px', fontWeight: 600, marginBottom: '6px', color: 'var(--color-ink-200)' }}
                >
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock
                    size={16}
                    color="var(--color-ink-400)"
                    style={{ position: 'absolute', left: '12px', top: '12px' }}
                  />
                  <input
                    id="login-password"
                    type="password"
                    value={passwordInput}
                    onChange={(e) => setPasswordInput(e.target.value)}
                    placeholder="Enter password"
                    style={{
                      width: '100%',
                      padding: '10px 12px 10px 38px',
                      borderRadius: '6px',
                      background: 'var(--color-ink-900)',
                      border: errors.password ? '1px solid var(--color-crit-red)' : '1px solid var(--color-ink-700)',
                      color: '#fff',
                      fontSize: '14px',
                      fontFamily: 'var(--font-sans)',
                      outline: 'none',
                    }}
                  />
                </div>
                {errors.password && (
                  <p style={{ fontSize: '12px', color: 'var(--color-crit-red)', margin: '4px 0 0', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <AlertCircle size={12} /> {errors.password}
                  </p>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={loginMutation.isPending}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  padding: '10px',
                  background: 'var(--color-trafo-blue)',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: 600,
                  cursor: loginMutation.isPending ? 'not-allowed' : 'pointer',
                  opacity: loginMutation.isPending ? 0.7 : 1,
                  fontFamily: 'var(--font-sans)',
                  marginTop: '8px',
                }}
              >
                {loginMutation.isPending ? (
                  <>
                    <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                    <span>Signing in...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In</span>
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>

            {/* Demo Fast Login Buttons */}
            <div style={{ marginTop: '24px', paddingTop: '16px', borderTop: '1px solid var(--color-ink-800)' }}>
              <p style={{ fontSize: '11px', color: 'var(--color-ink-400)', textTransform: 'uppercase', marginBottom: '8px', textAlign: 'center' }}>
                Judge / Demo Quick Fill
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('operator', 'operator123')}
                  style={{
                    padding: '6px 10px',
                    background: 'var(--color-ink-900)',
                    border: '1px solid var(--color-ink-700)',
                    borderRadius: '4px',
                    color: 'var(--color-ink-200)',
                    fontSize: '12px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  ⚡ <strong>Operator</strong>: operator / operator123
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('driver', 'driver123')}
                  style={{
                    padding: '6px 10px',
                    background: 'var(--color-ink-900)',
                    border: '1px solid var(--color-ink-700)',
                    borderRadius: '4px',
                    color: 'var(--color-ink-200)',
                    fontSize: '12px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  🚗 <strong>Driver</strong>: driver / driver123
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickLogin('judge', 'judge123')}
                  style={{
                    padding: '6px 10px',
                    background: 'var(--color-ink-900)',
                    border: '1px solid var(--color-ink-700)',
                    borderRadius: '4px',
                    color: 'var(--color-ink-200)',
                    fontSize: '12px',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  ⚖️ <strong>Judge</strong>: judge / judge123
                </button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default LoginPage
