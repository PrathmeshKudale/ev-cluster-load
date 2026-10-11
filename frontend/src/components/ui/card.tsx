import React from 'react'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  elevated?: boolean
  severity?: 'normal' | 'warn' | 'crit'
}

export const Card: React.FC<CardProps> = ({
  elevated = false,
  severity = 'normal',
  style,
  className = '',
  children,
  ...props
}) => {
  const severityBorders: Record<string, string> = {
    normal: '1px solid var(--color-ink-700)',
    warn: '2px solid var(--color-warn-amber)',
    crit: '2px solid var(--color-crit-red)',
  }

  const baseStyle: React.CSSProperties = {
    backgroundColor: elevated ? 'var(--color-ink-750)' : 'var(--color-ink-850)',
    border: severityBorders[severity],
    borderRadius: 'var(--radius-md)',
    padding: '16px',
    boxShadow: elevated ? '0 4px 12px rgba(0,0,0,0.3)' : '0 2px 6px rgba(0,0,0,0.2)',
    transition: 'border-color 0.2s ease, transform 0.15s ease',
    ...style,
  }

  return (
    <div style={baseStyle} className={`ui-card ${className}`} {...props}>
      {children}
    </div>
  )
}

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  style,
  children,
  ...props
}) => (
  <div
    style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: '12px',
      gap: '8px',
      ...style,
    }}
    {...props}
  >
    {children}
  </div>
)

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({
  style,
  children,
  ...props
}) => (
  <h3
    style={{
      fontSize: '17px',
      fontWeight: 700,
      color: 'var(--color-ink-100)',
      margin: 0,
      fontFamily: 'var(--font-sans)',
      ...style,
    }}
    {...props}
  >
    {children}
  </h3>
)

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({
  style,
  children,
  ...props
}) => (
  <p
    style={{
      fontSize: '13px',
      color: 'var(--color-ink-300)',
      margin: '2px 0 0',
      ...style,
    }}
    {...props}
  >
    {children}
  </p>
)

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  style,
  children,
  ...props
}) => (
  <div style={{ ...style }} {...props}>
    {children}
  </div>
)
