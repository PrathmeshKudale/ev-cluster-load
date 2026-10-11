import React from 'react'

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'warning'
  size?: 'sm' | 'md' | 'lg'
  icon?: React.ReactNode
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', icon, className = '', children, ...props }, ref) => {
    const baseStyle: React.CSSProperties = {
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      borderRadius: 'var(--radius-md)',
      fontFamily: 'var(--font-sans)',
      fontWeight: 700,
      cursor: props.disabled ? 'not-allowed' : 'pointer',
      opacity: props.disabled ? 0.5 : 1,
      transition: 'all 0.15s ease-in-out',
      border: 'none',
      textDecoration: 'none',
      userSelect: 'none',
    }

    const sizeStyles: Record<string, React.CSSProperties> = {
      sm: { padding: '6px 12px', fontSize: '13px' },
      md: { padding: '10px 18px', fontSize: '15px', minHeight: '44px' },
      lg: { padding: '14px 24px', fontSize: '16px', minHeight: '48px' },
    }

    const variantStyles: Record<string, React.CSSProperties> = {
      primary: {
        backgroundColor: 'var(--color-trafo-blue)',
        color: '#ffffff',
        boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
      },
      secondary: {
        backgroundColor: 'var(--color-ink-700)',
        color: 'var(--color-ink-100)',
      },
      outline: {
        backgroundColor: 'transparent',
        color: 'var(--color-ink-100)',
        border: '1px solid var(--color-ink-600)',
      },
      ghost: {
        backgroundColor: 'transparent',
        color: 'var(--color-ink-300)',
      },
      danger: {
        backgroundColor: 'var(--color-crit-red)',
        color: '#ffffff',
      },
      warning: {
        backgroundColor: 'var(--color-warn-amber)',
        color: '#ffffff',
      },
    }

    return (
      <button
        ref={ref}
        style={{ ...baseStyle, ...sizeStyles[size], ...variantStyles[variant] }}
        className={`ui-button ${className}`}
        {...props}
      >
        {icon && <span style={{ display: 'inline-flex' }}>{icon}</span>}
        {children}
      </button>
    )
  }
)

Button.displayName = 'Button'
