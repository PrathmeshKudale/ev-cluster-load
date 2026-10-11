import React from 'react'

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'normal' | 'warn' | 'crit' | 'brand' | 'neutral'
  icon?: React.ReactNode
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  icon,
  style,
  children,
  className = '',
  ...props
}) => {
  const variantStyles: Record<string, React.CSSProperties> = {
    normal: {
      backgroundColor: 'var(--color-safe-green-bg)',
      color: 'var(--color-safe-green)',
      border: '1px solid var(--color-safe-green-border)',
    },
    warn: {
      backgroundColor: 'var(--color-warn-amber-bg)',
      color: 'var(--color-warn-amber)',
      border: '1px solid var(--color-warn-amber-border)',
    },
    crit: {
      backgroundColor: 'var(--color-crit-red-bg)',
      color: 'var(--color-crit-red)',
      border: '1px solid var(--color-crit-red-border)',
    },
    brand: {
      backgroundColor: 'var(--color-trafo-blue-tint)',
      color: 'var(--color-trafo-blue)',
      border: '1px solid var(--color-trafo-blue)',
    },
    neutral: {
      backgroundColor: 'var(--color-ink-700)',
      color: 'var(--color-ink-200)',
      border: '1px solid var(--color-ink-600)',
    },
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '3px 8px',
        borderRadius: 'var(--radius-sm)',
        fontSize: '12px',
        fontWeight: 700,
        fontFamily: 'var(--font-sans)',
        whiteSpace: 'nowrap',
        ...variantStyles[variant],
        ...style,
      }}
      className={`ui-badge ${className}`}
      {...props}
    >
      {icon && <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>}
      {children}
    </span>
  )
}
