import React from 'react'
import { useForecast, useStations, useTransformerRisk } from '@/lib/queries'
import { ForecastBandChart } from '@/features/forecast/ForecastBandChart'
import { StationCard } from '@/features/cluster/StationCard'
import { AlertFeed } from '@/features/transformer/AlertFeed'
import { TransformerGauge } from '@/features/transformer/TransformerGauge'
import { PageLoader, PageError } from '@/components/PageStates'
import { forecastFixture, type ForecastFixture } from '@/fixtures/forecastFixture'
import { stationsFixture, type StationDetailFixture } from '@/fixtures/stationsFixture'
import { transformerFixture } from '@/fixtures/transformerFixture'
import { Cpu, RefreshCw } from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { useUIStore } from '@/store/uiStore'

export const OperatorPage: React.FC = () => {
  const navigate = useNavigate()
  const showToast = useUIStore((s) => s.showToast)
  const { data: forecastData, isLoading: forecastLoading, error: forecastError, refetch: refetchForecast } = useForecast()
  const { data: stationsData, isLoading: stationsLoading, error: stationsError, refetch: refetchStations } = useStations()
  const { data: riskData, isLoading: riskLoading, error: riskError, refetch: refetchRisk } = useTransformerRisk('T1')

  if (forecastLoading || stationsLoading || riskLoading) {
    return <PageLoader label="Loading grid telemetry and forecast models..." />
  }

  if (forecastError || stationsError || riskError) {
    return (
      <PageError
        error={(forecastError as Error) || (stationsError as Error) || (riskError as Error)}
        reset={() => {
          refetchForecast()
          refetchStations()
          refetchRisk()
        }}
      />
    )
  }

  // Active forecast mapping
  const activeForecast: ForecastFixture = forecastData
    ? {
        ...forecastFixture,
        hours: forecastData.hours,
        p10: forecastData.p10,
        p50: forecastData.p50,
        p90: forecastData.p90,
        warn_limit_pct: forecastData.warn,
        crit_limit_pct: forecastData.critical,
        model_version: forecastData.model_version,
      }
    : forecastFixture

  // Active stations mapping
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
          utilization_percent: item.utilization_pct ?? existing?.utilization_percent ?? 55,
          erlang_c_wait_min: (item.queue_count ?? 0) > 0 ? 5.8 : (existing?.erlang_c_wait_min ?? 1.5),
          active_sessions: existing?.active_sessions ?? Math.round(item.chargers * 0.5),
          current_active_kw: existing?.current_active_kw ?? Math.round(item.chargers * item.kw * 0.5),
          chargers: existing?.chargers ?? [],
        }
      })
    : stationsFixture

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Operator Title Bar */}
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
            Control Room • Substation Operator Overview
          </h1>
          <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '4px' }}>
            Feeder TX-100kVA • Conformal prediction bounds (α=0.10) • Active load derating
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={() => {
              refetchForecast()
              refetchStations()
              refetchRisk()
              showToast('Substation telemetry refreshed (Forecast, Stations, Transformer T1)', 'success')
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
            <span>Refresh Telemetry</span>
          </button>
          <Link
            to="/operator/transformer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              background: 'rgba(30, 136, 229, 0.15)',
              border: '1px solid var(--color-trafo-blue)',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '12px',
              fontWeight: 600,
              textDecoration: 'none',
            }}
          >
            <Cpu size={13} />
            <span>Transformer Monitor</span>
          </Link>
        </div>
      </div>

      {/* Grid: 2 cols on wide screens (Forecast chart + Alerts & Quick Gauge) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
          gap: '24px',
        }}
      >
        {/* Forecast Band Chart */}
        <section aria-label="Load Forecast Chart">
          <ForecastBandChart data={activeForecast} />
        </section>

        {/* Transformer Gauge & Alerts Feed */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <TransformerGauge
            data={{
              ...transformerFixture,
              loading_percent: riskData?.peak_p90_pct ?? transformerFixture.loading_percent,
              rating_kva: riskData?.kva ?? 100,
            }}
            warnThreshold={riskData?.warn_threshold_pct ?? 80}
            critThreshold={riskData?.crit_threshold_pct ?? 90}
          />
          <AlertFeed
            onAction={(item) => {
              if (item.action_label?.toLowerCase().includes('reroute') || item.entity_type === 'station') {
                showToast(`Rerouting drivers away from ${item.entity_id || 'station'}... Initiating dispatch`, 'info')
                navigate('/driver/recommend')
              } else if (item.action_label?.toLowerCase().includes('headroom') || item.entity_type === 'transformer') {
                showToast('Reviewing transformer thermal headroom...', 'info')
                navigate('/operator/transformer')
              } else {
                showToast(`Action dispatched: ${item.action_label || 'Resolved'}`, 'success')
              }
            }}
            onAcknowledge={(alertId) => {
              showToast(`Alert ${alertId} acknowledged`, 'info')
            }}
          />
        </div>
      </div>

      {/* Feeder Stations Grid */}
      <section aria-label="Stations in Feeder Zone">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, margin: 0, color: 'var(--color-ink-100)' }}>
            Feeder Connected Charging Stations ({stationsList.length})
          </h2>
          <span style={{ fontSize: '12px', color: 'var(--color-ink-400)' }}>
            Click a station to view detailed diagnostics
          </span>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '16px',
          }}
        >
          {stationsList.map((st) => (
            <Link
              key={st.id}
              to={`/operator/stations/${st.id}`}
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <StationCard station={st} />
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}

export default OperatorPage
