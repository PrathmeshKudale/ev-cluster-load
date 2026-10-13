import React from 'react'
import { useClusters, useStations } from '@/lib/queries'
import { useUIStore } from '@/store/uiStore'
import { ClusterMap } from '@/features/cluster/ClusterMap'
import { StationCard } from '@/features/cluster/StationCard'
import { PageLoader, PageError } from '@/components/PageStates'
import { clusterFixture } from '@/fixtures/clusterFixture'
import { stationsFixture, type StationDetailFixture } from '@/fixtures/stationsFixture'
import { MapPin, Navigation } from 'lucide-react'
import { Link } from 'react-router-dom'

export const DriverPage: React.FC = () => {
  const selectedStationId = useUIStore((s) => s.selectedStationId)
  const setSelectedStationId = useUIStore((s) => s.setSelectedStationId)

  const { data: _clustersData, isLoading: clusterLoading, error: clusterError, refetch: refetchClusters } = useClusters()
  const { data: stationsData, isLoading: stationsLoading, error: stationsError, refetch: refetchStations } = useStations()

  if (clusterLoading || stationsLoading) {
    return <PageLoader label="Loading cluster map and station data..." />
  }

  if (clusterError || stationsError) {
    return (
      <PageError
        error={(clusterError as Error) || (stationsError as Error)}
        reset={() => {
          refetchClusters()
          refetchStations()
        }}
      />
    )
  }

  // Use API stations if returned, otherwise fallback to fixture
  const stationsList: StationDetailFixture[] = stationsData?.items && stationsData.items.length > 0
    ? stationsData.items.map((item) => {
        const existing = stationsFixture.find((s) => s.id === item.id)
        return {
          id: item.id,
          name: item.name,
          cluster_id: 'C1',
          chargers_count: item.chargers,
          kw_per_charger: item.kw,
          detour_min: item.detour,
          latitude: item.latitude ?? existing?.latitude ?? 12.9716,
          longitude: item.longitude ?? existing?.longitude ?? 77.5946,
          utilization_percent: item.utilization_pct ?? existing?.utilization_percent ?? 50,
          erlang_c_wait_min: (item.queue_count ?? 0) > 0 ? 5.8 : (existing?.erlang_c_wait_min ?? 0.0),
          active_sessions: existing?.active_sessions ?? Math.round(item.chargers * 0.5),
          current_active_kw: existing?.current_active_kw ?? Math.round(item.chargers * item.kw * 0.5),
          chargers: existing?.chargers ?? [],
        }
      })
    : stationsFixture

  const showToast = useUIStore((s) => s.showToast)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Top Banner with Quick Action */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
          background: 'linear-gradient(90deg, rgba(30, 136, 229, 0.12) 0%, rgba(10, 31, 36, 0.4) 100%)',
          border: '1px solid var(--color-ink-700)',
          borderRadius: '10px',
          padding: '16px 20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              padding: '10px',
              borderRadius: '8px',
              background: 'var(--color-trafo-blue)',
              color: '#fff',
            }}
          >
            <MapPin size={22} />
          </div>
          <div>
            <h1 style={{ fontSize: '18px', fontWeight: 700, margin: 0, color: '#fff' }}>
              Substation Cluster Station Map
            </h1>
            <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', margin: '2px 0 0' }}>
              Select a hub on the radial topology to inspect wait times, chargers, and detour.
            </p>
          </div>
        </div>
        <Link
          to="/driver/recommend"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 16px',
            borderRadius: '6px',
            background: 'var(--color-trafo-blue)',
            color: '#fff',
            fontSize: '13px',
            fontWeight: 600,
            textDecoration: 'none',
          }}
        >
          <Navigation size={15} />
          <span>Get Smart Recommendation</span>
        </Link>
      </div>

      {/* Cluster Map SVG */}
      <section aria-label="Interactive Cluster Map">
        <ClusterMap
          data={clusterFixture}
          selectedStationId={selectedStationId}
          onSelectStation={(id) => {
            setSelectedStationId(id)
            const st = stationsList.find((s) => s.id === id)
            if (st) showToast(`Selected ${st.name} (${st.id}) on Cluster Map`, 'info')
          }}
        />
      </section>

      {/* Stations Grid */}
      <section aria-label="Available Charging Hubs">
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px', color: 'var(--color-ink-100)' }}>
          Active Stations in Feeder Zone ({stationsList.length})
        </h2>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
            gap: '16px',
          }}
        >
          {stationsList.map((station) => (
            <div
              key={station.id}
              style={{
                borderRadius: '8px',
                border: selectedStationId === station.id ? '2px solid var(--color-trafo-blue)' : '2px solid transparent',
                transition: 'border 0.15s ease',
              }}
            >
              <StationCard
                station={station}
                selected={selectedStationId === station.id}
                onSelect={(id) => {
                  setSelectedStationId(id)
                  showToast(`Selected ${station.name} (${station.id})`, 'info')
                }}
              />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}

export default DriverPage
