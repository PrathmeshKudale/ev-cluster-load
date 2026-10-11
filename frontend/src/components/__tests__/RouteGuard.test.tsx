import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { RouteGuard } from '../RouteGuard'
import { useUIStore } from '../../store/uiStore'

describe('F4: RouteGuard and role-based access control', () => {
  beforeEach(() => {
    useUIStore.setState({
      persona: 'driver',
      userRole: null,
      accessToken: null,
    })
  })

  it('redirects driver to /unauthorized when trying to access operator routes', () => {
    useUIStore.setState({ persona: 'driver', userRole: 'driver' })

    render(
      <MemoryRouter initialEntries={['/operator']}>
        <Routes>
          <Route element={<RouteGuard require="operator" />}>
            <Route path="/operator" element={<div>Operator Control Room</div>} />
          </Route>
          <Route path="/unauthorized" element={<div>Access Denied Unauthorized</div>} />
        </Routes>
      </MemoryRouter>
    )

    // Should NOT render operator content
    expect(screen.queryByText('Operator Control Room')).not.toBeInTheDocument()
    // Should redirect to unauthorized
    expect(screen.getByText('Access Denied Unauthorized')).toBeInTheDocument()
  })

  it('allows operator through to operator routes', () => {
    useUIStore.setState({ persona: 'operator', userRole: 'operator' })

    render(
      <MemoryRouter initialEntries={['/operator']}>
        <Routes>
          <Route element={<RouteGuard require="operator" />}>
            <Route path="/operator" element={<div>Operator Control Room</div>} />
          </Route>
          <Route path="/unauthorized" element={<div>Access Denied Unauthorized</div>} />
        </Routes>
      </MemoryRouter>
    )

    // Should render operator content
    expect(screen.getByText('Operator Control Room')).toBeInTheDocument()
  })
})
