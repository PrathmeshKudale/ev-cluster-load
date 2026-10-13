import React, { lazy } from 'react'
import { createBrowserRouter, Navigate, useRouteError } from 'react-router-dom'
import { RootLayout } from './components/RootLayout'
import { RouteGuard } from './components/RouteGuard'
import { PageLoader, PageError } from './components/PageStates'
import { useUIStore } from './store/uiStore'

// Lazy-loaded pages
const DriverPage = lazy(() => import('./pages/DriverPage'))
const DriverRecommendPage = lazy(() => import('./pages/DriverRecommendPage'))
const OperatorPage = lazy(() => import('./pages/OperatorPage'))
const OperatorTransformerPage = lazy(() => import('./pages/OperatorTransformerPage'))
const OperatorStationPage = lazy(() => import('./pages/OperatorStationPage'))
const ReplayPage = lazy(() => import('./pages/ReplayPage'))
const AboutPage = lazy(() => import('./pages/AboutPage'))
const LoginPage = lazy(() => import('./pages/LoginPage'))
const UnauthorizedPage = lazy(() => import('./pages/UnauthorizedPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const ComponentsPage = lazy(() => import('./pages/ComponentsPage'))

// Root index redirector based on current persona
const HomeRedirect: React.FC = () => {
  const persona = useUIStore((s) => s.persona)
  return <Navigate to={persona === 'operator' ? '/operator' : '/driver'} replace />
}

const RootErrorBoundary: React.FC = () => {
  const error = useRouteError() as Error
  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-ink-950)', display: 'grid', placeItems: 'center', padding: '24px' }}>
      <PageError
        error={error}
        reset={() => {
          window.location.href = import.meta.env.BASE_URL || '/'
        }}
      />
    </div>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RootErrorBoundary />,
    children: [
      {
        index: true,
        element: <HomeRedirect />,
      },
      // Public & Driver Routes
      {
        path: 'driver',
        element: <DriverPage />,
      },
      {
        path: 'driver/recommend',
        element: <DriverRecommendPage />,
      },
      {
        path: 'replay',
        element: <ReplayPage />,
      },
      {
        path: 'about',
        element: <AboutPage />,
      },
      {
        path: 'components',
        element: <ComponentsPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'unauthorized',
        element: <UnauthorizedPage />,
      },

      // Protected Operator Routes (Driver cannot access)
      {
        element: <RouteGuard require="operator" />,
        children: [
          {
            path: 'operator',
            element: <OperatorPage />,
          },
          {
            path: 'operator/transformer',
            element: <OperatorTransformerPage />,
          },
          {
            path: 'operator/stations/:id',
            element: <OperatorStationPage />,
          },
        ],
      },

      // 404 Catch-All
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
], {
  basename: import.meta.env.BASE_URL,
})
