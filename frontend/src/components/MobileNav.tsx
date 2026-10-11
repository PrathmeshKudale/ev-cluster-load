/**
 * Mobile bottom navigation bar — visible on narrow viewports (<768px).
 * Shows primary driver and operator destinations.
 */
import React from 'react'
import { NavLink } from 'react-router-dom'
import { Zap, MapPin, Activity, Cpu, History } from 'lucide-react'
import { useUIStore } from '../store/uiStore'

const driverNav = [
  { to: '/driver/recommend', icon: Zap, label: 'Recommend' },
  { to: '/driver', icon: MapPin, label: 'Map' },
  { to: '/about', icon: Activity, label: 'About' },
]

const operatorNav = [
  { to: '/operator', icon: Activity, label: 'Overview' },
  { to: '/operator/transformer', icon: Cpu, label: 'Transformer' },
  { to: '/replay', icon: History, label: 'Replay' },
]

export const MobileNav: React.FC = () => {
  const persona = useUIStore((s) => s.persona)
  const navItems = persona === 'operator' ? operatorNav : driverNav

  return (
    <nav
      aria-label="Mobile Navigation"
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        background: 'rgba(10, 31, 36, 0.95)',
        backdropFilter: 'blur(10px)',
        borderTop: '1px solid var(--color-ink-700)',
        display: 'flex',
        alignItems: 'stretch',
        // Hidden on desktop
      }}
      className="mobile-nav"
    >
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to.split('/').length === 2}
          aria-label={label}
          style={({ isActive }) => ({
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '4px',
            padding: '10px 4px 12px',
            fontSize: '10px',
            fontWeight: 600,
            textDecoration: 'none',
            color: isActive ? 'var(--color-trafo-blue)' : 'var(--color-ink-300)',
            borderTop: isActive ? '2px solid var(--color-trafo-blue)' : '2px solid transparent',
            transition: 'color 0.15s ease',
          })}
        >
          <Icon size={20} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
