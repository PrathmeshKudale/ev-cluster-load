import React, { Suspense } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import {
  Zap,
  Activity,
  MapPin,
  Cpu,
  History,
  Grid,
  User,
  Shield,
  Info,
  LogIn,
  LogOut,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { useUIStore, type UserPersona } from '@/store/uiStore'
import { useUrlState } from '@/hooks/useUrlState'
import { useWebSocket } from '@/lib/useWebSocket'
import { Breadcrumbs } from '@/components/Breadcrumbs'
import { MobileNav } from '@/components/MobileNav'
import { PageLoader } from '@/components/PageStates'

export const RootLayout: React.FC = () => {
  // Sync URL search params with store
  useUrlState()
  // Connect WebSocket for live updates
  useWebSocket(true)

  const navigate = useNavigate()
  const location = useLocation()

  const persona = useUIStore((s) => s.persona)
  const setPersona = useUIStore((s) => s.setPersona)
  const accessToken = useUIStore((s) => s.accessToken)
  const username = useUIStore((s) => s.username)
  const setAccessToken = useUIStore((s) => s.setAccessToken)
  const setUserRole = useUIStore((s) => s.setUserRole)
  const setUsername = useUIStore((s) => s.setUsername)
  const toastMessage = useUIStore((s) => s.toastMessage)
  const clearToast = useUIStore((s) => s.clearToast)

  const handlePersonaChange = (newPersona: UserPersona) => {
    setPersona(newPersona)
    if (newPersona === 'driver' && location.pathname.startsWith('/operator')) {
      navigate('/driver')
    } else if (newPersona === 'operator' && location.pathname.startsWith('/driver')) {
      navigate('/operator')
    }
  }

  const handleLogout = () => {
    setAccessToken(null)
    setUserRole(null)
    setUsername(null)
    navigate('/login')
  }

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
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div
          role="status"
          style={{
            position: 'fixed',
            top: '72px',
            right: '20px',
            zIndex: 100,
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            padding: '10px 16px',
            borderRadius: '8px',
            background:
              toastMessage.variant === 'error'
                ? 'rgba(239, 68, 68, 0.92)'
                : toastMessage.variant === 'success'
                ? 'rgba(16, 185, 129, 0.92)'
                : 'rgba(30, 136, 229, 0.92)',
            color: '#ffffff',
            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
            backdropFilter: 'blur(8px)',
            fontSize: '13px',
            fontWeight: 500,
            maxWidth: '380px',
          }}
        >
          <span style={{ flex: 1 }}>{toastMessage.message}</span>
          <button
            onClick={clearToast}
            aria-label="Dismiss toast"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#fff',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              padding: '2px',
            }}
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Sticky Top Header */}
      <header
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 40,
          background: 'rgba(10, 31, 36, 0.94)',
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
          <NavLink
            to="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              flexShrink: 0,
              textDecoration: 'none',
              color: 'inherit',
            }}
          >
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
          </NavLink>

          {/* Nav Tabs (Desktop) */}
          <nav
            aria-label="Main Navigation"
            className="desktop-nav"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              overflowX: 'auto',
              padding: '4px 0',
            }}
          >
            <NavLink
              to="/driver/recommend"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--color-ink-300)',
                background: isActive ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <Zap size={14} />
              <span>Recommend</span>
            </NavLink>

            <NavLink
              to="/driver"
              end
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--color-ink-300)',
                background: isActive ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <MapPin size={14} />
              <span>Cluster Map</span>
            </NavLink>

            <NavLink
              to="/operator"
              end
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--color-ink-300)',
                background: isActive ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <Activity size={14} />
              <span>Operator Overview</span>
            </NavLink>

            <NavLink
              to="/operator/transformer"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--color-ink-300)',
                background: isActive ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <Cpu size={14} />
              <span>Transformer</span>
            </NavLink>

            <NavLink
              to="/replay"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--color-ink-300)',
                background: isActive ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <History size={14} />
              <span>Replay</span>
            </NavLink>

            <NavLink
              to="/about"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? '#ffffff' : 'var(--color-ink-300)',
                background: isActive ? 'var(--color-ink-800)' : 'transparent',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-ink-600)' : '1px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <Info size={14} />
              <span>About</span>
            </NavLink>

            <div style={{ width: '1px', height: '24px', background: 'var(--color-ink-700)', margin: '0 4px' }} />

            <NavLink
              to="/components"
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 12px',
                fontSize: '13px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--color-trafo-blue)' : '#a5f3fc',
                background: isActive ? 'rgba(30, 136, 229, 0.18)' : 'rgba(30, 136, 229, 0.08)',
                borderRadius: '6px',
                border: isActive ? '1px solid var(--color-trafo-blue)' : '1px solid rgba(30, 136, 229, 0.3)',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              })}
            >
              <Grid size={14} />
              <span>/components</span>
              <Badge variant="brand" style={{ fontSize: '10px', padding: '1px 5px' }}>
                Catalog
              </Badge>
            </NavLink>
          </nav>

          {/* Right Controls: Persona Switcher & Auth */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            {/* Persona Switcher */}
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
                onClick={() => handlePersonaChange('driver')}
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
                onClick={() => handlePersonaChange('operator')}
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

            {/* Auth Link / Status */}
            {accessToken ? (
              <button
                onClick={handleLogout}
                title={`Logged in as ${username ?? 'User'}. Click to log out.`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  color: 'var(--color-ink-300)',
                  background: 'transparent',
                  border: '1px solid var(--color-ink-700)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                }}
              >
                <LogOut size={12} />
                <span className="desktop-nav">{username ?? 'Logout'}</span>
              </button>
            ) : (
              <NavLink
                to="/login"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  fontSize: '12px',
                  color: 'var(--color-trafo-blue)',
                  background: 'rgba(30, 136, 229, 0.08)',
                  border: '1px solid rgba(30, 136, 229, 0.3)',
                  borderRadius: '6px',
                  textDecoration: 'none',
                }}
              >
                <LogIn size={12} />
                <span className="desktop-nav">Login</span>
              </NavLink>
            )}
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
          padding: '16px 20px 64px',
        }}
      >
        <div style={{ marginBottom: '16px' }}>
          <Breadcrumbs />
        </div>
        <Suspense fallback={<PageLoader label="Loading section..." />}>
          <Outlet />
        </Suspense>
      </main>

      {/* Mobile Bottom Navigation */}
      <MobileNav />

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
          </div>
        </div>
      </footer>
    </div>
  )
}
