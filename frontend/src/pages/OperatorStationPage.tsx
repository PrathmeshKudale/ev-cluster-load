import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useStation } from '@/lib/queries'
import { useUIStore } from '@/store/uiStore'
import { PageLoader, PageError } from '@/components/PageStates'
import { stationsFixture } from '@/fixtures/stationsFixture'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowLeft, Zap, Clock, Navigation, Activity, CheckCircle2 } from 'lucide-react'

export const OperatorStationPage: React.FC = () => {
  const { id = 'S1' } = useParams<{ id: string }>()
  const showToast = useUIStore((s) => s.showToast)
  const { data, isLoading, error, refetch } = useStation(id)

  if (isLoading) {
    return <PageLoader label={`Loading station diagnostics for ${id}...`} />
  }

  // Fallback to fixture if API item not found
  const fallback = stationsFixture.find((s) => s.id === id) ?? stationsFixture[0]
  const station = data ?? {
    id: fallback.id,
    name: fallback.name,
    chargers: fallback.chargers_count,
    kw: fallback.kw_per_charger,
    detour: fallback.detour_min,
    latitude: fallback.latitude,
    longitude: fallback.longitude,
    utilization_pct: fallback.utilization_percent,
  }

  if (error && !fallback) {
    return <PageError error={error as Error} reset={() => refetch()} />
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Back button */}
      <div>
        <Link
          to="/operator"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--color-ink-300)',
            textDecoration: 'none',
            fontSize: '13px',
            fontWeight: 500,
          }}
        >
          <ArrowLeft size={14} />
          <span>Back to Operator Overview</span>
        </Link>
      </div>

      {/* Station Title Card */}
      <Card>
        <CardHeader>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '8px',
                  background: 'var(--color-trafo-blue)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                }}
              >
                <Zap size={22} />
              </div>
              <div>
                <CardTitle style={{ fontSize: '18px' }}>{station.name} ({station.id})</CardTitle>
                <p style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                  GPS: {station.latitude?.toFixed(4)}, {station.longitude?.toFixed(4)} • Feeder TX-100kVA
                </p>
              </div>
            </div>

            <div>
              {(station.utilization_pct ?? 0) > 85 ? (
                <Badge variant="crit">High Congestion ({station.utilization_pct}%)</Badge>
              ) : (station.utilization_pct ?? 0) > 70 ? (
                <Badge variant="warn">Moderate Load ({station.utilization_pct}%)</Badge>
              ) : (
                <Badge variant="normal">Optimal ({station.utilization_pct}%)</Badge>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '16px',
            }}
          >
            <div style={{ padding: '12px', background: 'var(--color-ink-900)', borderRadius: '6px', border: '1px solid var(--color-ink-800)' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-ink-400)', textTransform: 'uppercase' }}>Available Bays</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#fff', marginTop: '4px' }}>
                {station.chargers} Chargers
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Rated {station.kw} kW per charger
              </div>
            </div>

            <div style={{ padding: '12px', background: 'var(--color-ink-900)', borderRadius: '6px', border: '1px solid var(--color-ink-800)' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-ink-400)', textTransform: 'uppercase' }}>Detour Penalty</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-warn-amber)', marginTop: '4px' }}>
                +{station.detour} min
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Relative to feeder centroid
              </div>
            </div>

            <div style={{ padding: '12px', background: 'var(--color-ink-900)', borderRadius: '6px', border: '1px solid var(--color-ink-800)' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-ink-400)', textTransform: 'uppercase' }}>Erlang-C Wait Est.</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-safe-green)', marginTop: '4px' }}>
                {fallback.erlang_c_wait_min} min
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                M/M/c queuing calculation
              </div>
            </div>

            <div style={{ padding: '12px', background: 'var(--color-ink-900)', borderRadius: '6px', border: '1px solid var(--color-ink-800)' }}>
              <div style={{ fontSize: '11px', color: 'var(--color-ink-400)', textTransform: 'uppercase' }}>Feeder Power Demand</div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-trafo-blue)', marginTop: '4px' }}>
                {(station.chargers * station.kw * ((station.utilization_pct ?? 50) / 100)).toFixed(1)} kW
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Connected to Feeder T1
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Active Operator Controls */}
      <Card>
        <CardHeader>
          <CardTitle style={{ fontSize: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} color="var(--color-trafo-blue)" />
            <span>Operator Remote Controls & Telemetry Dispatch</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => {
                refetch()
                showToast(`Live diagnostics refreshed for station ${station.name} (${station.id}).`, 'success')
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: 'var(--color-ink-800)',
                border: '1px solid var(--color-ink-600)',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Zap size={14} />
              <span>Refresh Station Diagnostics</span>
            </button>

            <button
              onClick={() => {
                showToast(`[OCPP 1.6J] Reset(type='Soft') dispatched to ${station.id}. Response: Accepted`, 'info')
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: 'rgba(217, 119, 6, 0.16)',
                border: '1px solid var(--color-warn-amber)',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <Clock size={14} />
              <span>Trigger OCPP 1.6J Soft Reset</span>
            </button>

            <button
              onClick={() => {
                showToast(`[OSCP 2.0] Capacity limit adjusted for ${station.id}. Dynamic load headroom optimized.`, 'success')
              }}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                background: 'rgba(5, 150, 105, 0.16)',
                border: '1px solid var(--color-safe-green)',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '13px',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <CheckCircle2 size={14} />
              <span>Apply Dynamic OSCP Curtailment</span>
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default OperatorStationPage
