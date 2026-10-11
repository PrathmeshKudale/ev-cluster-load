import React from 'react'
import { AlertCircle, AlertTriangle, CheckCircle2, Info } from 'lucide-react'

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'warn' | 'crit' | 'success'
  title: string
  description?: string
  action?: React.ReactNode
}

export const Alert: React.FC<AlertProps> = ({
  variant = 'info',
  title,
  description,
  action,
  style,
  ...props
}) => {
  const variantConfig = {
    info: {
      bg: 'var(--color-trafo-blue-tint)',
      border: 'var(--color-trafo-blue)',
      color: 'var(--color-trafo-blue)',
      icon: <Info size={20} />,
    },
    warn: {
      bg: 'var(--color-warn-amber-bg)',
      border: 'var(--color-warn-amber)',
      color: 'var(--color-warn-amber)',
      icon: <AlertTriangle size={20} />,
    },
    crit: {
      bg: 'var(--color-crit-red-bg)',
      border: 'var(--color-crit-red)',
      color: 'var(--color-crit-red)',
      icon: <AlertCircle size={20} />,
    },
    success: {
      bg: 'var(--color-safe-green-bg)',
      border: 'var(--color-safe-green)',
      color: 'var(--color-safe-green)',
      icon: <CheckCircle2 size={20} />,
    },
  }

  const cfg = variantConfig[variant]

  return (
    <div
      role="alert"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '14px 16px',
        borderRadius: 'var(--radius-md)',
        backgroundColor: cfg.bg,
        border: `1px solid ${cfg.border}`,
        color: 'var(--color-ink-100)',
        ...style,
      }}
      {...props}
    >
      <div style={{ color: cfg.color, flexShrink: 0, marginTop: '2px' }}>{cfg.icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ fontWeight: 700, fontSize: '15px' }}>{title}</div>
        {description && (
          <div style={{ fontSize: '13px', color: 'var(--color-ink-200)', marginTop: '4px' }}>
            {description}
          </div>
        )}
      </div>
      {action && <div style={{ flexShrink: 0 }}>{action}</div>}
    </div>
  )
}
