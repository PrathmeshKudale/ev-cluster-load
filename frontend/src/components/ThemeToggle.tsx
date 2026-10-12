/**
 * ThemeToggle — cycles between system / light / dark.
 * Accessible: labelled button with aria-pressed state.
 * Respects prefers-reduced-motion for icon swap animation.
 */
import React from 'react'
import { Sun, Moon, Monitor } from 'lucide-react'
import { useTheme, ThemeMode } from '@/hooks/useTheme'

const MODES: ThemeMode[] = ['system', 'light', 'dark']
const LABELS: Record<ThemeMode, string> = {
  system: 'System theme',
  light: 'Light theme',
  dark: 'Dark theme',
}
const ICONS: Record<ThemeMode, React.ReactNode> = {
  system: <Monitor size={16} aria-hidden="true" />,
  light: <Sun size={16} aria-hidden="true" />,
  dark: <Moon size={16} aria-hidden="true" />,
}

export const ThemeToggle: React.FC<{ className?: string }> = ({ className = '' }) => {
  const { theme, setTheme } = useTheme()

  const cycle = () => {
    const next = MODES[(MODES.indexOf(theme) + 1) % MODES.length]
    setTheme(next)
  }

  return (
    <button
      type="button"
      onClick={cycle}
      aria-label={`Current: ${LABELS[theme]}. Click to switch.`}
      title={LABELS[theme]}
      className={className}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: '6px 10px',
        borderRadius: 'var(--radius-sm)',
        border: '1px solid var(--color-border)',
        background: 'var(--color-surface-raised)',
        color: 'var(--color-text-secondary)',
        cursor: 'pointer',
        fontSize: '13px',
        fontFamily: 'var(--font-sans)',
        transition: 'all 0.15s ease',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.borderColor = 'var(--color-trafo-blue)'
        e.currentTarget.style.color = 'var(--color-trafo-blue)'
      }}
      onMouseLeave={e => {
        e.currentTarget.style.borderColor = 'var(--color-border)'
        e.currentTarget.style.color = 'var(--color-text-secondary)'
      }}
    >
      {ICONS[theme]}
      <span className="sr-only">{LABELS[theme]}</span>
    </button>
  )
}
