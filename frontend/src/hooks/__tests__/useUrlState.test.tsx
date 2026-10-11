import React from 'react'
import { render } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { useUrlState } from '../useUrlState'
import { useUIStore } from '../../store/uiStore'

const TestUrlConsumer: React.FC = () => {
  useUrlState()
  return <div>URL State Synced</div>
}

describe('F3: URL state persistence and restoration', () => {
  beforeEach(() => {
    useUIStore.setState({
      driverMode: 'balanced',
      selectedStationId: 'S1',
      persona: 'driver',
    })
  })

  it('restores driverMode, station, and persona from a copied URL', () => {
    render(
      <MemoryRouter initialEntries={['/driver/recommend?mode=grid_friendly&station=S3&persona=operator']}>
        <TestUrlConsumer />
      </MemoryRouter>
    )

    const state = useUIStore.getState()
    expect(state.driverMode).toBe('grid_friendly')
    expect(state.selectedStationId).toBe('S3')
    expect(state.persona).toBe('operator')
  })
})
