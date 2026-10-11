import React from 'react'
import { useSimulationMetrics } from '@/lib/queries'
import { ReplayControls } from '@/features/replay/ReplayControls'
import { PageLoader, PageError } from '@/components/PageStates'
import { replayFixture } from '@/fixtures/replayFixture'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { TrendingDown, Clock, ShieldCheck } from 'lucide-react'

export const ReplayPage: React.FC = () => {
  const { data: _metricsData, isLoading, error, refetch } = useSimulationMetrics()

  if (isLoading) {
    return <PageLoader label="Loading simulation trace and benchmark comparison..." />
  }

  if (error) {
    return <PageError error={error as Error} reset={() => refetch()} />
  }

  const m = replayFixture.metrics
  const imp = replayFixture.metrics.improvement

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div>
        <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0, color: '#fff' }}>
          Simulation Trace Replay & Benchmark Comparison
        </h1>
        <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '4px' }}>
          Compare FCFS unmanaged arrivals against GridFlow AHP + OR-Tools CP-SAT smart guidance.
        </p>
      </div>

      {/* Interactive Controls */}
      <section aria-label="Playback Controller">
        <ReplayControls />
      </section>

      {/* Benchmark Comparison Cards */}
      <section aria-label="Benchmark Metrics">
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '14px', color: 'var(--color-ink-100)' }}>
          Historical Day Benchmark Comparison (200 EV Arrivals)
        </h2>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '16px',
          }}
        >
          {/* Peak Load Card */}
          <Card>
            <CardHeader>
              <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px' }}>
                <TrendingDown size={18} color="var(--color-safe-green)" />
                <span>Peak Transformer Load</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>Unmanaged (FCFS):</span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-crit-red)' }}>
                  {m.fcfs.peak_load_kw} kW (Overloaded)
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>Smart Guided:</span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-safe-green)' }}>
                  {m.smart.peak_load_kw} kW (Safe)
                </span>
              </div>
              <div style={{ padding: '8px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--color-safe-green)' }}>
                Peak shaving achieved: -{imp.peak_shaving_kw} kW (-{imp.peak_shaving_pct}%) headroom preserved.
              </div>
            </CardContent>
          </Card>

          {/* Wait Time Card */}
          <Card>
            <CardHeader>
              <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px' }}>
                <Clock size={18} color="var(--color-trafo-blue)" />
                <span>Mean Driver Wait Time</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>Unmanaged (FCFS):</span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-warn-amber)' }}>
                  {m.fcfs.mean_wait_min} min
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>Smart Guided:</span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-safe-green)' }}>
                  {m.smart.mean_wait_min} min
                </span>
              </div>
              <div style={{ padding: '8px', background: 'rgba(30, 136, 229, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--color-trafo-blue)' }}>
                Wait reduction: -{imp.wait_reduction_pct}% queuing delay via Erlang-C balancing.
              </div>
            </CardContent>
          </Card>

          {/* Overload Violations Card */}
          <Card>
            <CardHeader>
              <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px' }}>
                <ShieldCheck size={18} color="var(--color-safe-green)" />
                <span>Overload Hours (&gt;90% Critical)</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>Unmanaged (FCFS):</span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-crit-red)' }}>
                  {m.fcfs.overload_crit_hours} hrs
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>Smart Guided:</span>
                <span style={{ fontSize: '15px', fontWeight: 700, color: 'var(--color-safe-green)' }}>
                  {m.smart.overload_crit_hours} hrs
                </span>
              </div>
              <div style={{ padding: '8px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '6px', fontSize: '12px', color: 'var(--color-safe-green)' }}>
                Grid reliability: {imp.overload_eliminated_pct}% critical overload events eliminated.
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}

export default ReplayPage
