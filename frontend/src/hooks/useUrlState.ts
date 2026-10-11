/**
 * useUrlState hook
 * Syncs shareable filter parameters (driverMode, selectedStationId, alertFilter, persona)
 * to/from the URL search params so that copying the URL restores the same view.
 *
 * Usage: call once in the top-level page component.
 */
import { useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useUIStore, type DriverMode, type UserPersona } from '../store/uiStore'

const VALID_MODES: DriverMode[] = ['fastest', 'balanced', 'grid_friendly']
const VALID_PERSONAS: UserPersona[] = ['driver', 'operator']

export function useUrlState() {
  const [searchParams, setSearchParams] = useSearchParams()

  const setDriverMode = useUIStore((s) => s.setDriverMode)
  const setSelectedStationId = useUIStore((s) => s.setSelectedStationId)
  const setAlertFilter = useUIStore((s) => s.setAlertFilter)
  const setPersona = useUIStore((s) => s.setPersona)

  const driverMode = useUIStore((s) => s.driverMode)
  const selectedStationId = useUIStore((s) => s.selectedStationId)
  const alertFilter = useUIStore((s) => s.alertFilter)
  const persona = useUIStore((s) => s.persona)

  // Hydrate store from URL on first mount
  useEffect(() => {
    const mode = searchParams.get('mode') as DriverMode | null
    const station = searchParams.get('station')
    const filter = searchParams.get('filter') as 'all' | 'active' | 'crit' | null
    const personaParam = searchParams.get('persona') as UserPersona | null

    if (mode && VALID_MODES.includes(mode)) setDriverMode(mode)
    if (station) setSelectedStationId(station)
    if (filter && ['all', 'active', 'crit'].includes(filter)) setAlertFilter(filter)
    if (personaParam && VALID_PERSONAS.includes(personaParam)) setPersona(personaParam)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Write store state back to URL whenever it changes
  useEffect(() => {
    const next = new URLSearchParams(searchParams.toString())
    next.set('mode', driverMode)
    if (selectedStationId !== 'S1') next.set('station', selectedStationId)
    else next.delete('station')
    if (alertFilter !== 'all') next.set('filter', alertFilter)
    else next.delete('filter')
    next.set('persona', persona)
    setSearchParams(next, { replace: true })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [driverMode, selectedStationId, alertFilter, persona])
}
