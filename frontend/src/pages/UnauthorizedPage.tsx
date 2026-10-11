import React from 'react'
import { Link } from 'react-router-dom'
import { ShieldAlert, ArrowLeft, LogIn } from 'lucide-react'
import { useUIStore } from '@/store/uiStore'

export const UnauthorizedPage: React.FC = () => {
  const persona = useUIStore((s) => s.persona)
  const setPersona = useUIStore((s) => s.setPersona)

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '400px',
        textAlign: 'center',
        padding: '32px 16px',
        gap: '16px',
      }}
    >
      <div
        style={{
          width: '56px',
          height: '56px',
          borderRadius: '12px',
          background: 'rgba(239, 68, 68, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-crit-red)',
        }}
      >
        <ShieldAlert size={32} />
      </div>
      <div>
        <h1 style={{ fontSize: '22px', fontWeight: 700, margin: '0 0 8px', color: '#fff' }}>
          403 — Operator Access Restricted
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--color-ink-300)', maxWidth: '440px', margin: '0 auto 20px' }}>
          Driver accounts cannot access feeder substation telemetry or operator controls. Switch to Operator mode or sign in with an operator credential.
        </p>
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
        <button
          onClick={() => setPersona('operator')}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            background: 'var(--color-trafo-blue)',
            color: '#fff',
            border: 'none',
            fontSize: '13px',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Switch to Operator Persona
        </button>

        <Link
          to="/login"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            borderRadius: '6px',
            background: 'var(--color-ink-800)',
            border: '1px solid var(--color-ink-600)',
            color: 'var(--color-ink-200)',
            fontSize: '13px',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          <LogIn size={14} />
          <span>Sign In as Operator</span>
        </Link>

        <Link
          to="/driver"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            borderRadius: '6px',
            background: 'transparent',
            border: '1px solid var(--color-ink-700)',
            color: 'var(--color-ink-300)',
            fontSize: '13px',
            fontWeight: 500,
            textDecoration: 'none',
          }}
        >
          <ArrowLeft size={14} />
          <span>Return to Driver Map</span>
        </Link>
      </div>
    </div>
  )
}

export default UnauthorizedPage
