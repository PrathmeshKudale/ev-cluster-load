import React from 'react'
import {
  Zap,
  Activity,
  MapPin,
  Cpu,
  History,
  Grid,
  User,
  Shield,
  ExternalLink,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'

export type NavTab = 'recommend' | 'map' | 'operator' | 'transformer' | 'replay' | 'components'
export type UserPersona = 'driver' | 'operator'

export interface AppShellProps {
  currentTab: NavTab
  onSelectTab: (tab: NavTab) => void
  persona: UserPersona
  onSelectPersona: (persona: UserPersona) => void
  children: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onSelectTab,
  persona,
  onSelectPersona,
  children,
}) => {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: 'var(--color-ink-950)',
        color: 'var(--color-ink-50)',
        fontFamily: 'var(--font-sans)',
      }}
    >
      {/* Top Header */}
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 40,
          background: 'rgba(10, 31, 36, 0.92)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          borderBottom: '1px solid var(--color-ink-700)',
          padding: '0 20px',
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            height: '64px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          {/* Logo & Cluster Branding */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--color-trafo-blue) 0%, #0d47a1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(30, 136, 229, 0.35)',
              }}
            >
              <Zap size={22} color="#ffffff" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '16px', fontWeight: 700, letterSpacing: '-0.01em' }}>
                  GridFlow EV
                </span>
                <span
                  style={{
                    fontSize: '11px',
                    fontWeight: 600,
                    padding: '2px 6px',
                    background: 'var(--color-ink-800)',
                    color: 'var(--color-ink-300)',
                    borderRadius: '4px',
                  }}
                >
                  TX-100kVA
                </span>
              </div>
              <div
                style={{
                  fontSize: '11px',
                  color: 'var(--color-ink-300)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <span
                  style={{
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: 'var(--color-safe-green)',
                    display: 'inline-block',
                  }}
                />
                <span>Metro Central C1</span>
                <span>•</span>
                <span style={{ color: 'var(--color-warn-amber)' }}>78.1% Load</span>
              </div>
            </div>
          </div>

          {/* Nav Tabs */}
          <nav
            aria-label="Main Navigation"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              overflowX: 'auto',
              padding: '4px 0',
            }}
          >
            <button
              onClick={() => onSelectTab('recommend')}
              className="app-nav-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: currentTab === 'recommend' ? 600 : 500,
                color: currentTab === 'recommend' ? '#ffffff' : 'var(--color-ink-300)',
                background: currentTab === 'recommend' ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: currentTab === 'recommend' ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <Zap size={14} color={currentTab === 'recommend' ? 'var(--color-trafo-blue)' : undefined} />
              <span>Recommend</span>
            </button>

            <button
              onClick={() => onSelectTab('map')}
              className="app-nav-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: currentTab === 'map' ? 600 : 500,
                color: currentTab === 'map' ? '#ffffff' : 'var(--color-ink-300)',
                background: currentTab === 'map' ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: currentTab === 'map' ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <MapPin size={14} color={currentTab === 'map' ? 'var(--color-trafo-blue)' : undefined} />
              <span>Cluster Map</span>
            </button>

            <button
              onClick={() => onSelectTab('operator')}
              className="app-nav-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: currentTab === 'operator' ? 600 : 500,
                color: currentTab === 'operator' ? '#ffffff' : 'var(--color-ink-300)',
                background: currentTab === 'operator' ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: currentTab === 'operator' ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <Activity size={14} color={currentTab === 'operator' ? 'var(--color-trafo-blue)' : undefined} />
              <span>Operator Overview</span>
            </button>

            <button
              onClick={() => onSelectTab('transformer')}
              className="app-nav-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: currentTab === 'transformer' ? 600 : 500,
                color: currentTab === 'transformer' ? '#ffffff' : 'var(--color-ink-300)',
                background: currentTab === 'transformer' ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: currentTab === 'transformer' ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <Cpu size={14} color={currentTab === 'transformer' ? 'var(--color-trafo-blue)' : undefined} />
              <span>Transformer</span>
            </button>

            <button
              onClick={() => onSelectTab('replay')}
              className="app-nav-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: currentTab === 'replay' ? 600 : 500,
                color: currentTab === 'replay' ? '#ffffff' : 'var(--color-ink-300)',
                background: currentTab === 'replay' ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: currentTab === 'replay' ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <History size={14} color={currentTab === 'replay' ? 'var(--color-trafo-blue)' : undefined} />
              <span>Replay</span>
            </button>

            <div style={{ width: '1px', height: '24px', background: 'var(--color-ink-700)', margin: '0 4px' }} />

            {/* /components link button */}
            <button
              onClick={() => onSelectTab('components')}
              className="app-nav-button"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: currentTab === 'components' ? 600 : 500,
                color: currentTab === 'components' ? 'var(--color-trafo-blue)' : '#a5f3fc',
                background:
                  currentTab === 'components'
                    ? 'rgba(30, 136, 229, 0.18)'
                    : 'rgba(30, 136, 229, 0.08)',
                borderRadius: '6px',
                border:
                  currentTab === 'components'
                    ? '1px solid var(--color-trafo-blue)'
                    : '1px solid rgba(30, 136, 229, 0.3)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              <Grid size={14} />
              <span>/components</span>
              <Badge variant="brand" style={{ fontSize: '10px', padding: '1px 5px' }}>
                Catalog
              </Badge>
            </button>
          </nav>

          {/* Right Controls: Persona Switcher */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: 'var(--color-ink-900)',
                border: '1px solid var(--color-ink-700)',
                borderRadius: '6px',
                padding: '2px',
              }}
            >
              <button
                onClick={() => onSelectPersona('driver')}
                aria-label="Switch to Driver view"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  fontWeight: persona === 'driver' ? 600 : 500,
                  color: persona === 'driver' ? '#ffffff' : 'var(--color-ink-400)',
                  background: persona === 'driver' ? 'var(--color-ink-700)' : 'transparent',
                  borderRadius: '4px',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <User size={12} />
                <span>Driver</span>
              </button>
              <button
                onClick={() => onSelectPersona('operator')}
                aria-label="Switch to Operator view"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  fontWeight: persona === 'operator' ? 600 : 500,
                  color: persona === 'operator' ? '#ffffff' : 'var(--color-ink-400)',
                  background: persona === 'operator' ? 'var(--color-ink-700)' : 'transparent',
                  borderRadius: '4px',
                  border: 'none',
                  cursor: 'pointer',
                }}
              >
                <Shield size={12} />
                <span>Operator</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main
        id="main-content"
        style={{
          flex: 1,
          maxWidth: '1440px',
          width: '100%',
          margin: '0 auto',
          padding: '24px 20px 48px',
        }}
      >
        {children}
      </main>

      {/* Footer */}
      <footer
        style={{
          borderTop: '1px solid var(--color-ink-800)',
          background: 'var(--color-ink-900)',
          padding: '16px 20px',
          fontSize: '12px',
          color: 'var(--color-ink-400)',
        }}
      >
        <div
          style={{
            maxWidth: '1440px',
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div>
            <span>GridFlow EV Substation Intelligence</span>
            <span style={{ margin: '0 8px' }}>•</span>
            <span>Feeder TX-100kVA</span>
            <span style={{ margin: '0 8px' }}>•</span>
            <span>Derating Factor: 0.982</span>
            <span style={{ margin: '0 8px' }}>•</span>
            <span>Pandapower Feeder V-Drop: 3.49%</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ color: 'var(--color-ink-300)' }}>Atkinson Hyperlegible • WCAG AA</span>
            <button
              onClick={() => onSelectTab('components')}
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--color-trafo-blue)',
                cursor: 'pointer',
                fontSize: '12px',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: 0,
              }}
            >
              <span>View Component Library</span>
              <ExternalLink size={12} />
            </button>
          </div>
        </div>
      </footer>
    </div>
  )
}
