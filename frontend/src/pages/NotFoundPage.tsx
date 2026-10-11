import React from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, Home } from 'lucide-react'

export const NotFoundPage: React.FC = () => {
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
          background: 'rgba(30, 136, 229, 0.15)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-trafo-blue)',
        }}
      >
        <AlertCircle size={32} />
      </div>
      <div>
        <h1 style={{ fontSize: '24px', fontWeight: 700, margin: '0 0 8px', color: '#fff' }}>
          404 — Page Not Found
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--color-ink-300)', maxWidth: '400px', margin: '0 auto 20px' }}>
          The requested route does not exist on the GridFlow EV Substation platform.
        </p>
      </div>

      <Link
        to="/"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '10px 18px',
          borderRadius: '6px',
          background: 'var(--color-trafo-blue)',
          color: '#fff',
          fontSize: '14px',
          fontWeight: 600,
          textDecoration: 'none',
        }}
      >
        <Home size={16} />
        <span>Return Home</span>
      </Link>
    </div>
  )
}

export default NotFoundPage
