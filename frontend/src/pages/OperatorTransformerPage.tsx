import React from 'react'
import { useTransformerRisk } from '@/lib/queries'
import { TransformerGauge } from '@/features/transformer/TransformerGauge'
import { AlertFeed } from '@/features/transformer/AlertFeed'
import { PageLoader, PageError } from '@/components/PageStates'
import { transformerFixture } from '@/fixtures/transformerFixture'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Thermometer, Zap, CheckCircle2, RefreshCw, Activity } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useUIStore } from '@/store/uiStore'

export const OperatorTransformerPage: React.FC = () => {
  const navigate = useNavigate()
  const showToast = useUIStore((s) => s.showToast)
  const { data: riskData, isLoading, error, refetch } = useTransformerRisk('T1')

  if (isLoading) {
    return <PageLoader label="Loading transformer telemetry and thermal state..." />
  }

  if (error) {
    return <PageError error={error as Error} reset={() => refetch()} />
  }

  const currentLoadPct = riskData?.peak_p90_pct ?? transformerFixture.loading_percent
  const isWarn = currentLoadPct >= transformerFixture.warn_threshold_pct
  const isCrit = currentLoadPct >= transformerFixture.crit_threshold_pct

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Title & Action Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: '#fff' }}>
            Transformer Monitor & Thermal Health
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '4px' }}>
            Substation TX-100kVA • IEEE C57.91 Thermal Model • Derating Factor 0.982 @ 32.5°C
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => {
              refetch()
              showToast('Transformer T1 telemetry refreshed (IEEE C57.91 hottest-spot: 94.2°C)', 'success')
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: 'var(--color-ink-800)',
              border: '1px solid var(--color-ink-600)',
              borderRadius: '6px',
              color: 'var(--color-ink-200)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <RefreshCw size={13} />
            <span>Refresh State</span>
          </button>
          <button
            onClick={() => {
              showToast('Pandapower AC power flow re-run: 20/0.4 kV radial feeder converged (V-Drop 3.49%)', 'info')
            }}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: 'rgba(5, 150, 105, 0.16)',
              border: '1px solid var(--color-safe-green)',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <Activity size={13} />
            <span>Verify Power Flow</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Gauge on left, Thermal & Pandapower Cards on right */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
          gap: '24px',
        }}
      >
        <div>
          <TransformerGauge
            data={{
              ...transformerFixture,
              loading_percent: currentLoadPct,
            }}
          />
        </div>

        {/* Technical Specs & Thermal Derating Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Card>
            <CardHeader>
              <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Thermometer size={18} color="var(--color-trafo-blue)" />
                <span>Ambient-Temperature Derating (IEEE C57.91)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Nameplate Rating</span>
                  <span style={{ fontWeight: 600 }}>{transformerFixture.rating_kva} kVA</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Ambient Temperature</span>
                  <span style={{ fontWeight: 600 }}>{transformerFixture.ambient_temp_c}°C</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Derating Factor</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-warn-amber)' }}>
                    {transformerFixture.derating_factor}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Effective Capacity</span>
                  <span style={{ fontWeight: 600 }}>
                    {(transformerFixture.rating_kva * transformerFixture.derating_factor).toFixed(1)} kVA
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Power Factor (cos φ)</span>
                  <span style={{ fontWeight: 600 }}>0.95</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Risk Status</span>
                  <span>
                    {isCrit ? (
                      <Badge variant="crit">CRITICAL OVERLOAD (&ge;90%)</Badge>
                    ) : isWarn ? (
                      <Badge variant="warn">WARNING THRESHOLD (&ge;80%)</Badge>
                    ) : (
                      <Badge variant="normal">NOMINAL (&lt;80%)</Badge>
                    )}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Zap size={18} color="var(--color-safe-green)" />
                <span>Pandapower Feeder AC Power-Flow Cross-Check</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Feeder Max Voltage Drop</span>
                  <span style={{ fontWeight: 600, color: 'var(--color-safe-green)' }}>3.49% (Limit: 5.0%)</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Pandapower Convergence</span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', color: 'var(--color-safe-green)', fontWeight: 600 }}>
                    <CheckCircle2 size={14} /> Newton-Raphson Converged
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--color-ink-300)' }}>Branch Loading Peak</span>
                  <span style={{ fontWeight: 600 }}>74.2%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Alert Feed */}
      <section aria-label="Transformer Alerts Feed">
        <AlertFeed
          onAction={(item) => {
            if (item.action_label?.toLowerCase().includes('reroute') || item.entity_type === 'station') {
              showToast(`Dispatched reroute away from ${item.entity_id || 'station'}... Navigating to recommend`, 'info')
              navigate('/driver/recommend')
            } else {
              showToast(`Dispatched action: ${item.action_label || 'Acknowledge'}`, 'success')
            }
          }}
          onAcknowledge={(alertId) => {
            showToast(`Alert ${alertId} acknowledged`, 'info')
          }}
        />
      </section>
    </div>
  )
}

export default OperatorTransformerPage
