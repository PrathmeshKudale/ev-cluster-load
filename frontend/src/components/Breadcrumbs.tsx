/**
 * Breadcrumbs component — shows path segments on desktop (≥768px).
 * Uses React Router's useLocation.
 */
import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'

const LABEL_MAP: Record<string, string> = {
  driver: 'Driver',
  recommend: 'Recommend',
  operator: 'Operator',
  transformer: 'Transformer Monitor',
  stations: 'Stations',
  replay: 'Replay',
  about: 'About & Methodology',
  components: 'Component Library',
  login: 'Login',
}

export const Breadcrumbs: React.FC = () => {
  const { pathname } = useLocation()
  const segments = pathname.split('/').filter(Boolean)

  if (segments.length === 0) return null

  return (
    <nav
      aria-label="Breadcrumb"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '13px',
        color: 'var(--color-ink-300)',
        padding: '8px 0 0',
        flexWrap: 'wrap',
      }}
    >
      <Link
        to="/"
        style={{ color: 'var(--color-ink-300)', textDecoration: 'none' }}
        aria-label="Home"
      >
        GridFlow
      </Link>

      {segments.map((seg, i) => {
        const path = '/' + segments.slice(0, i + 1).join('/')
        const label = LABEL_MAP[seg] ?? seg.charAt(0).toUpperCase() + seg.slice(1)
        const isLast = i === segments.length - 1

        return (
          <React.Fragment key={path}>
            <ChevronRight size={12} style={{ opacity: 0.5 }} />
            {isLast ? (
              <span aria-current="page" style={{ color: 'var(--color-ink-100)', fontWeight: 600 }}>
                {label}
              </span>
            ) : (
              <Link
                to={path}
                style={{ color: 'var(--color-ink-300)', textDecoration: 'none' }}
              >
                {label}
              </Link>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}
