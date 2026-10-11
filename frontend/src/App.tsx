import { useState, useEffect } from 'react'
import {
  Zap,
} from 'lucide-react'
import { AppShell, type NavTab, type UserPersona } from '@/components/AppShell'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Alert } from '@/components/ui/alert'

// Feature Components
import { ClusterMap, StationCard } from '@/features/cluster'
import { ForecastBandChart } from '@/features/forecast'
import { TransformerGauge, AlertFeed } from '@/features/transformer'
import { RecommendationCard } from '@/features/recommend'
import { ReplayControls } from '@/features/replay'

// Fixtures
import { clusterFixture } from '@/fixtures/clusterFixture'
import { stationsFixture } from '@/fixtures/stationsFixture'
import { forecastFixture } from '@/fixtures/forecastFixture'
import { transformerFixture } from '@/fixtures/transformerFixture'
import { recommendationFixture, type CandidateRecommendation } from '@/fixtures/recommendationFixture'
import { replayFixture } from '@/fixtures/replayFixture'
import { alertFixture } from '@/fixtures/alertFixture'

// Catalog Page
import { ComponentsPage } from '@/pages/ComponentsPage'

export function App() {
  // Sync tab with URL pathname or hash (e.g., /components or #components)
  const getInitialTab = (): NavTab => {
    const path = window.location.pathname.toLowerCase()
    const hash = window.location.hash.toLowerCase()
    if (path.includes('/components') || hash.includes('components')) {
      return 'components'
    }
    if (path.includes('/map') || hash.includes('map')) {
      return 'map'
    }
    if (path.includes('/operator') || hash.includes('operator')) {
      return 'operator'
    }
    if (path.includes('/transformer') || hash.includes('transformer')) {
      return 'transformer'
    }
    if (path.includes('/replay') || hash.includes('replay')) {
      return 'replay'
    }
    return 'recommend'
  }

  const [currentTab, setCurrentTab] = useState<NavTab>(getInitialTab)
  const [persona, setPersona] = useState<UserPersona>('driver')
  const [driverMode, setDriverMode] = useState<'fastest' | 'balanced' | 'grid_friendly'>('balanced')
  const [selectedStationId, setSelectedStationId] = useState<string>('S1')
  const [bookingConfirmed, setBookingConfirmed] = useState<string | null>(null)

  // Listen to browser forward/back buttons
  useEffect(() => {
    const handlePopState = () => {
      setCurrentTab(getInitialTab())
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  const handleSelectTab = (tab: NavTab) => {
    setCurrentTab(tab)
    const targetPath = tab === 'components' ? '/components' : `/${tab === 'recommend' ? '' : tab}`
    if (window.location.pathname !== targetPath) {
      window.history.pushState(null, '', targetPath)
    }
  }

  const handleReserve = (rec: CandidateRecommendation) => {
    setBookingConfirmed(`${rec.station_name} (Plug ${rec.station_id}-P${rec.rank}) reserved! ETA: ${rec.starts_in_h === 0 ? 'Immediate' : `In ${rec.starts_in_h}h`}`)
    setTimeout(() => {
      setBookingConfirmed(null)
    }, 6000
    )
  }

  return (
    <AppShell
      currentTab={currentTab}
      onSelectTab={handleSelectTab}
      persona={persona}
      onSelectPersona={setPersona}
    >
      {/* Booking confirmation banner */}
      {bookingConfirmed && (
        <div style={{ marginBottom: '20px' }}>
          <Alert variant="success" title="Slot Confirmed (3-Tap Flow Complete!)">
            {bookingConfirmed} Feeder TX-100kVA allocation reserved. Navigation route dispatched.
          </Alert>
        </div>
      )}

      {/* 1. /components Catalog Page */}
      {currentTab === 'components' && <ComponentsPage />}

      {/* 2. Recommend Screen (Driver Focus: 3-Tap Dispatch Flow) */}
      {currentTab === 'recommend' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Hero / Mode Selector */}
          <section
            style={{
              background: 'linear-gradient(135deg, var(--color-ink-900) 0%, var(--color-ink-850) 100%)',
              border: '1px solid var(--color-ink-700)',
              borderRadius: 'var(--radius-lg)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                  <Badge variant="brand" icon={<Zap size={12} />}>
                    Driver 3-Tap Flow
                  </Badge>
                  <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>
                    TAP 1: Pick Mode • TAP 2: Inspect Why • TAP 3: Reserve Slot
                  </span>
                </div>
                <h1 style={{ fontSize: '26px', fontWeight: 700, margin: 0 }}>
                  Smart Charging Recommendation
                </h1>
                <p style={{ fontSize: '14px', color: 'var(--color-ink-300)', marginTop: '4px', margin: 0 }}>
                  AHP Pairwise Multi-Objective Optimization balancing your queue wait, detour, and transformer overload risk.
                </p>
              </div>

              {/* Mode Pills */}
              <div
                style={{
                  display: 'flex',
                  background: 'var(--color-ink-950)',
                  border: '1px solid var(--color-ink-700)',
                  borderRadius: 'var(--radius-md)',
                  padding: '4px',
                  gap: '4px',
                }}
              >
                <button
                  onClick={() => setDriverMode('fastest')}
                  className="app-nav-button"
                  style={{
                    padding: '8px 14px',
                    fontSize: '13px',
                    fontWeight: driverMode === 'fastest' ? 600 : 500,
                    color: driverMode === 'fastest' ? '#ffffff' : 'var(--color-ink-300)',
                    background: driverMode === 'fastest' ? 'var(--color-ink-750)' : 'transparent',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  ⚡ Fastest
                </button>
                <button
                  onClick={() => setDriverMode('balanced')}
                  className="app-nav-button"
                  style={{
                    padding: '8px 14px',
                    fontSize: '13px',
                    fontWeight: driverMode === 'balanced' ? 600 : 500,
                    color: driverMode === 'balanced' ? '#ffffff' : 'var(--color-ink-300)',
                    background: driverMode === 'balanced' ? 'var(--color-ink-750)' : 'transparent',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  ⚖️ Balanced (Recommended)
                </button>
                <button
                  onClick={() => setDriverMode('grid_friendly')}
                  className="app-nav-button"
                  style={{
                    padding: '8px 14px',
                    fontSize: '13px',
                    fontWeight: driverMode === 'grid_friendly' ? 600 : 500,
                    color: driverMode === 'grid_friendly' ? '#ffffff' : 'var(--color-ink-300)',
                    background: driverMode === 'grid_friendly' ? 'var(--color-ink-750)' : 'transparent',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                  }}
                >
                  🌱 Grid Friendly
                </button>
              </div>
            </div>
          </section>

          {/* Recommendation Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
              gap: '20px',
            }}
          >
            {recommendationFixture.top3.map((candidate) => (
              <RecommendationCard
                key={candidate.rank}
                recommendation={candidate}
                mode={driverMode}
                onReserve={handleReserve}
                highlight={candidate.rank === 1}
              />
            ))}
          </div>

          {/* Quick Map Preview */}
          <div style={{ marginTop: '12px' }}>
            <ClusterMap
              data={clusterFixture}
              onSelectStation={(id) => setSelectedStationId(id)}
            />
          </div>
        </div>
      )}

      {/* 3. Cluster Map Screen */}
      {currentTab === 'map' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <ClusterMap
            data={clusterFixture}
            onSelectStation={(id) => setSelectedStationId(id)}
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 600, color: 'var(--color-ink-100)' }}>
              Cluster Stations ({stationsFixture.length})
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
                gap: '16px',
              }}
            >
              {stationsFixture.map((st) => (
                <StationCard
                  key={st.id}
                  station={st}
                  selected={st.id === selectedStationId}
                  onSelect={(id) => setSelectedStationId(id)}
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 4. Operator Overview Screen */}
      {currentTab === 'operator' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Key Metric Tiles */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '16px',
            }}
          >
            <Card>
              <CardContent style={{ padding: '16px' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>TX-100kVA Current Load</span>
                <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--color-warn-amber)', marginTop: '4px' }}>
                  78.1 kVA
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-ink-400)', marginTop: '2px' }}>
                  78.1% of 100 kVA (Warn Limit: 80%)
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent style={{ padding: '16px' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Feeder Headroom</span>
                <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--color-safe-green)', marginTop: '4px' }}>
                  21.9 kVA
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-ink-400)', marginTop: '2px' }}>
                  Derated Capacity: 98.2 kVA
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent style={{ padding: '16px' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Cluster Active Sessions</span>
                <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--color-trafo-blue)', marginTop: '4px' }}>
                  14 Plugs
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-ink-400)', marginTop: '2px' }}>
                  58.3% Plugs In Use (14 of 24)
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent style={{ padding: '16px' }}>
                <span style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Pandapower Feeder V-Drop</span>
                <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--color-ink-100)', marginTop: '4px' }}>
                  3.49%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--color-safe-green)', marginTop: '2px' }}>
                  Safe (&lt; 5.0% Grid Code Limit)
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 24-Hour Forecast Band */}
          <ForecastBandChart data={forecastFixture} />

          {/* Two-Column Grid: Gauge & Alert Stream */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: '24px',
            }}
          >
            <TransformerGauge data={transformerFixture} />
            <AlertFeed alerts={alertFixture} />
          </div>
        </div>
      )}

      {/* 5. Transformer Screen */}
      {currentTab === 'transformer' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: '24px',
            }}
          >
            <TransformerGauge data={transformerFixture} />
            <AlertFeed alerts={alertFixture} />
          </div>

          <ForecastBandChart data={forecastFixture} />
        </div>
      )}

      {/* 6. Replay Screen */}
      {currentTab === 'replay' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <ReplayControls initialState={replayFixture} />

          <ForecastBandChart data={forecastFixture} />
        </div>
      )}
    </AppShell>
  )
}
export default App
