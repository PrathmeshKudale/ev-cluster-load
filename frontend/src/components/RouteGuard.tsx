/**
 * Route Guard component.
 * Prevents drivers from accessing operator routes and vice-versa.
 * Redirects to /login if unauthenticated (when auth is enforced).
 */
import React from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useUIStore } from '../store/uiStore'

export type RequiredRole = 'driver' | 'operator' | 'admin' | 'any'

interface RouteGuardProps {
  require?: RequiredRole
  /** If true, user MUST be authenticated (accessToken set) */
  requireAuth?: boolean
}

export const RouteGuard: React.FC<RouteGuardProps> = ({
  require = 'any',
  requireAuth = false,
}) => {
  const accessToken = useUIStore((s) => s.accessToken)
  const userRole = useUIStore((s) => s.userRole)
  const location = useLocation()

  // Auth check — only if backend auth is configured
  if (requireAuth && !accessToken) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Role check
  if (require !== 'any') {
    const roleHierarchy: Record<string, number> = {
      driver: 1,
      judge: 2,
      operator: 3,
      admin: 4,
    }
    const persona = useUIStore.getState().persona
    const effectiveRole = userRole ?? persona ?? 'driver'
    const required = roleHierarchy[require] ?? 1
    const current = roleHierarchy[effectiveRole] ?? 0
    if (current < required) {
      return <Navigate to="/unauthorized" replace />
    }
  }

  return <Outlet />
}
