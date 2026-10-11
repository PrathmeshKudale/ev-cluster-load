import React from 'react'

export interface TabItem {
  id: string
  label: string
  icon?: React.ReactNode
}

export interface TabsProps {
  items: TabItem[]
  activeId: string
  onChange: (id: string) => void
}

export const Tabs: React.FC<TabsProps> = ({ items, activeId, onChange }) => {
  return (
    <div
      role="tablist"
      style={{
        display: 'flex',
        backgroundColor: 'var(--color-ink-900)',
        padding: '4px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--color-ink-700)',
        gap: '4px',
        overflowX: 'auto',
      }}
    >
      {items.map((tab) => {
        const isActive = tab.id === activeId
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            style={{
              flex: 1,
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              padding: '8px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '14px',
              fontWeight: isActive ? 700 : 500,
              fontFamily: 'var(--font-sans)',
              border: 'none',
              cursor: 'pointer',
              backgroundColor: isActive ? 'var(--color-trafo-blue)' : 'transparent',
              color: isActive ? '#ffffff' : 'var(--color-ink-300)',
              transition: 'all 0.15s ease',
              whiteSpace: 'nowrap',
            }}
          >
            {tab.icon && <span style={{ display: 'inline-flex' }}>{tab.icon}</span>}
            {tab.label}
          </button>
        )
      })}
    </div>
  )
}
