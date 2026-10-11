import React, { useEffect } from 'react'
import { X } from 'lucide-react'

export interface DrawerProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description?: string
  children: React.ReactNode
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="drawer-title"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        backgroundColor: 'rgba(5, 19, 23, 0.75)',
        backdropFilter: 'blur(4px)',
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '85vh',
          backgroundColor: 'var(--color-ink-900)',
          borderTopLeftRadius: 'var(--radius-lg)',
          borderTopRightRadius: 'var(--radius-lg)',
          border: '1px solid var(--color-ink-700)',
          borderBottom: 'none',
          boxShadow: '0 -8px 32px rgba(0, 0, 0, 0.5)',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideUp 0.25s ease-out',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag handle pill */}
        <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '10px' }}>
          <div
            style={{
              width: '40px',
              height: '4px',
              backgroundColor: 'var(--color-ink-600)',
              borderRadius: '2px',
            }}
          />
        </div>

        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--color-ink-700)',
            display: 'flex',
            alignItems: 'flex-start',
            justifyContent: 'space-between',
            gap: '12px',
          }}
        >
          <div>
            <h2
              id="drawer-title"
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--color-ink-100)',
                margin: 0,
              }}
            >
              {title}
            </h2>
            {description && (
              <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '4px' }}>
                {description}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label="Close drawer"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-ink-300)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Body Content */}
        <div style={{ padding: '20px', flex: 1 }}>{children}</div>
      </div>
    </div>
  )
}
