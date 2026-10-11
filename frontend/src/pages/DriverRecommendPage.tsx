import React from 'react'
import { useRecommendations } from '@/lib/queries'
import { useUIStore, type DriverMode } from '@/store/uiStore'
import { RecommendationCard } from '@/features/recommend/RecommendationCard'
import { PageLoader, PageError } from '@/components/PageStates'
import { recommendationFixture } from '@/fixtures/recommendationFixture'
import { Zap, Clock, ShieldCheck, Scale } from 'lucide-react'

export const DriverRecommendPage: React.FC = () => {
  const driverMode = useUIStore((s) => s.driverMode)
  const setDriverMode = useUIStore((s) => s.setDriverMode)

  const { data: _recData, isLoading, error, refetch } = useRecommendations({ mode: driverMode })

  const modes: Array<{
    id: DriverMode
    label: string
    sublabel: string
    icon: typeof Zap
    desc: string
  }> = [
    {
      id: 'fastest',
      label: 'Fastest Route',
      sublabel: 'w1=0.60, w2=0.25',
      icon: Clock,
      desc: 'Minimizes wait and detour time. Ideal when in a hurry.',
    },
    {
      id: 'balanced',
      label: 'Balanced (Recommended)',
      sublabel: 'w1=0.35, w2=0.25',
      icon: Scale,
      desc: 'Balanced wait, detour, and cluster grid utilization.',
    },
    {
      id: 'grid_friendly',
      label: 'Grid Friendly',
      sublabel: 'w3=0.45, w4=0.30',
      icon: ShieldCheck,
      desc: 'Protects distribution transformer peak load. Off-peak discount eligible.',
    },
  ]

  if (isLoading) {
    return <PageLoader label="Calculating AHP weights and CP-SAT assignments..." />
  }

  if (error) {
    return <PageError error={error as Error} reset={() => refetch()} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header and Step Instructions */}
      <div>
        <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: '#fff' }}>
          Smart Charging Station Recommendation
        </h1>
        <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '4px' }}>
          Objective Function: <code style={{ color: 'var(--color-trafo-blue)' }}>J = w1·wait + w2·detour + w3·(1-util) + w4·risk</code>
        </p>
      </div>

      {/* Step 1: Mode Selector (Tap 1) */}
      <section aria-label="Step 1: Select Driver Profile">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <span
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: 'var(--color-trafo-blue)',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            1
          </span>
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ink-100)' }}>
            Choose Preference Profile (AHP Matrix)
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '12px',
          }}
        >
          {modes.map(({ id, label, sublabel, icon: Icon, desc }) => {
            const isSelected = driverMode === id
            return (
              <button
                key={id}
                onClick={() => setDriverMode(id)}
                aria-pressed={isSelected}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '14px 16px',
                  background: isSelected ? 'rgba(30, 136, 229, 0.14)' : 'var(--color-ink-900)',
                  border: isSelected ? '2px solid var(--color-trafo-blue)' : '1px solid var(--color-ink-700)',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                  color: 'inherit',
                }}
              >
                <div
                  style={{
                    padding: '8px',
                    borderRadius: '6px',
                    background: isSelected ? 'var(--color-trafo-blue)' : 'var(--color-ink-800)',
                    color: '#fff',
                    flexShrink: 0,
                  }}
                >
                  <Icon size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: isSelected ? '#fff' : 'var(--color-ink-200)' }}>
                    {label}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-ink-400)', marginTop: '2px' }}>
                    {sublabel}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '6px' }}>
                    {desc}
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </section>

      {/* Step 2: Recommendations Result (Tap 2: View Top Options, Tap 3: Why Drawer) */}
      <section aria-label="Step 2: Recommended Stations">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <span
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '50%',
              background: 'var(--color-trafo-blue)',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            2
          </span>
          <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-ink-100)' }}>
            Ranked Candidate Assignments (Consistency Ratio CR &lt; 0.10)
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {recommendationFixture.top3.map((rec) => (
            <RecommendationCard
              key={rec.station_id}
              recommendation={rec}
              mode={driverMode}
              highlight={rec.rank === 1}
            />
          ))}
        </div>
      </section>
    </div>
  )
}

export default DriverRecommendPage
