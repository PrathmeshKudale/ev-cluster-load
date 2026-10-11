/**
 * Shared loading/error skeletons used across lazy-loaded routes.
 */
import React from 'react'
import { AlertCircle, Loader2 } from 'lucide-react'

export const PageLoader: React.FC<{ label?: string }> = ({ label = 'Loading...' }) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '320px',
      gap: '16px',
      color: 'var(--color-ink-300)',
    }}
    role="status"
    aria-label={label}
  >
    <Loader2 size={36} color="var(--color-trafo-blue)" style={{ animation: 'spin 1s linear infinite' }} />
    <p style={{ fontSize: '14px' }}>{label}</p>
    <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
  </div>
)

export const PageError: React.FC<{ error?: Error | null; reset?: () => void }> = ({ error, reset }) => (
  <div
    style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '320px',
      gap: '16px',
      color: 'var(--color-ink-100)',
      textAlign: 'center',
    }}
    role="alert"
  >
    <AlertCircle size={40} color="var(--color-crit-red)" />
    <div>
      <p style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px' }}>Something went wrong</p>
      {error && <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginBottom: '16px' }}>{error.message}</p>}
    </div>
    {reset && (
      <button
        onClick={reset}
        style={{
          padding: '8px 20px',
          borderRadius: '6px',
          background: 'var(--color-trafo-blue)',
          color: '#fff',
          border: 'none',
          cursor: 'pointer',
          fontFamily: 'var(--font-sans)',
          fontWeight: 600,
        }}
      >
        Try Again
      </button>
    )}
  </div>
)
