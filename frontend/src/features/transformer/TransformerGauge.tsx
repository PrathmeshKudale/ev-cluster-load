import React from 'react'
import { Activity, ShieldCheck, Thermometer, Zap, AlertTriangle, AlertCircle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { transformerFixture, type TransformerFixture } from '@/fixtures/transformerFixture'

export interface TransformerGaugeProps {
  data?: TransformerFixture
}

export const TransformerGauge: React.FC<TransformerGaugeProps> = ({
  data = transformerFixture,
}) => {
  const pct = data.loading_percent
  const isCrit = pct >= data.crit_threshold_pct
  const isWarn = pct >= data.warn_threshold_pct && !isCrit

  // Semi-circle gauge geometry (180 degree arc from angle -180 to 0)
  const radius = 90
  const cx = 130
  const cy = 115
  const strokeWidth = 16

  // Circumference of semi-circle: PI * radius
  const arcLength = Math.PI * radius
  // Current fill length
  const fillLength = (Math.min(pct, 100) / 100) * arcLength
  const dashOffset = arcLength - fillLength

  // Arc needle angle: 0% is -180 deg, 100% is 0 deg
  const needleAngle = -180 + (Math.min(pct, 100) / 100) * 180
  const needleRad = (needleAngle * Math.PI) / 180
  const needleX = cx + (radius - 10) * Math.cos(needleRad)
  const needleY = cy + (radius - 10) * Math.sin(needleRad)

  let gaugeColor = 'var(--color-safe-green)'
  if (isCrit) gaugeColor = 'var(--color-crit-red)'
  else if (isWarn) gaugeColor = 'var(--color-warn-amber)'

  return (
    <Card style={{ width: '100%' }}>
      <CardHeader>
        <div>
          <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={20} color="var(--color-trafo-blue)" />
            <span>Transformer Monitor & Thermal Gauge</span>
          </CardTitle>
          <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
            {data.name} • Rating: {data.rating_kva} kVA • PF: {data.power_factor}
          </p>
        </div>
        <Badge
          variant={isCrit ? 'crit' : isWarn ? 'warn' : 'normal'}
          icon={isCrit ? <AlertCircle size={12} /> : isWarn ? <AlertTriangle size={12} /> : <ShieldCheck size={12} />}
        >
          {isCrit ? 'CRITICAL (>90%)' : isWarn ? 'WARNING (80-90%)' : 'NORMAL (<80%)'}
        </Badge>
      </CardHeader>

      <CardContent>
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '24px', alignItems: 'center' }}>
          {/* Radial Semi-Circle Gauge */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <svg width="260" height="150" viewBox="0 0 260 150">
              {/* Background Arc */}
              <path
                d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
                fill="none"
                stroke="var(--color-ink-750)"
                strokeWidth={strokeWidth}
                strokeLinecap="round"
              />

              {/* 80% Warning Arc Marker */}
              {/* 90% Critical Arc Marker */}
              <path
                d={`M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`}
                fill="none"
                stroke={gaugeColor}
                strokeWidth={strokeWidth}
                strokeDasharray={`${fillLength} ${dashOffset}`}
                strokeLinecap="round"
                style={{ transition: 'stroke-dasharray 0.5s ease' }}
              />

              {/* Threshold tick markers at 80% and 90% */}
              {/* 80% angle = -180 + 0.8 * 180 = -36 deg */}
              {/* 90% angle = -180 + 0.9 * 180 = -18 deg */}
              <line
                x1={cx + (radius - 12) * Math.cos((-36 * Math.PI) / 180)}
                y1={cy + (radius - 12) * Math.sin((-36 * Math.PI) / 180)}
                x2={cx + (radius + 12) * Math.cos((-36 * Math.PI) / 180)}
                y2={cy + (radius + 12) * Math.sin((-36 * Math.PI) / 180)}
                stroke="var(--color-warn-amber)"
                strokeWidth="2.5"
              />
              <line
                x1={cx + (radius - 12) * Math.cos((-18 * Math.PI) / 180)}
                y1={cy + (radius - 12) * Math.sin((-18 * Math.PI) / 180)}
                x2={cx + (radius + 12) * Math.cos((-18 * Math.PI) / 180)}
                y2={cy + (radius + 12) * Math.sin((-18 * Math.PI) / 180)}
                stroke="var(--color-crit-red)"
                strokeWidth="2.5"
              />

              {/* Center Needle Indicator */}
              <line
                x1={cx}
                y1={cy}
                x2={needleX}
                y2={needleY}
                stroke="var(--color-ink-100)"
                strokeWidth="3"
                strokeLinecap="round"
              />
              <circle cx={cx} cy={cy} r="6" fill="var(--color-ink-100)" />

              {/* Center Percentage Text */}
              <text
                x={cx}
                y={cy - 12}
                textAnchor="middle"
                fill="var(--color-ink-100)"
                fontSize="26"
                fontWeight="700"
                fontFamily="var(--font-mono)"
              >
                {pct.toFixed(1)}%
              </text>
              <text
                x={cx}
                y={cy + 8}
                textAnchor="middle"
                fill="var(--color-ink-300)"
                fontSize="12"
                fontFamily="var(--font-sans)"
              >
                {data.current_apparent_kva.toFixed(1)} / {data.rating_kva} kVA
              </text>
            </svg>

            {/* Scale legend */}
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                width: '210px',
                fontSize: '11px',
                color: 'var(--color-ink-300)',
                marginTop: '-8px',
              }}
            >
              <span>0%</span>
              <span style={{ color: 'var(--color-warn-amber)' }}>80% Warn</span>
              <span style={{ color: 'var(--color-crit-red)' }}>90% Crit</span>
              <span>100%</span>
            </div>
          </div>

          {/* Grid Health & Environmental Tile Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '12px' }}>
            <div
              style={{
                padding: '12px',
                backgroundColor: 'var(--color-ink-900)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-ink-700)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--color-ink-300)' }}>
                <Thermometer size={14} color="var(--color-warn-amber)" />
                <span>Ambient Derating</span>
              </div>
              <div style={{ fontSize: '16px', fontWeight: 700, marginTop: '4px' }}>
                {data.ambient_temp_c}°C • {(data.derating_factor * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Effective Limit: {data.effective_kva.toFixed(1)} kVA
              </div>
            </div>

            <div
              style={{
                padding: '12px',
                backgroundColor: 'var(--color-ink-900)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-ink-700)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--color-ink-300)' }}>
                <Activity size={14} color="var(--color-trafo-blue)" />
                <span>Pandapower AC Flow</span>
              </div>
              <div style={{ fontSize: '16px', fontWeight: 700, marginTop: '4px' }}>
                {data.pandapower.converged ? 'CONVERGED' : 'FAILED'}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Max V-Drop: {data.pandapower.max_voltage_drop_pct}% (Limit: &lt;5%)
              </div>
            </div>

            <div
              style={{
                padding: '12px',
                backgroundColor: 'var(--color-ink-900)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-ink-700)',
              }}
            >
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Active Power Draw</div>
              <div className="font-mono-numbers" style={{ fontSize: '16px', fontWeight: 700, marginTop: '4px' }}>
                {data.current_active_kw} kW
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Feeder Losses: {data.pandapower.transformer_losses_kw} kW
              </div>
            </div>

            <div
              style={{
                padding: '12px',
                backgroundColor: 'var(--color-ink-900)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-ink-700)',
              }}
            >
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Peak 24h P90 Risk</div>
              <div
                className="font-mono-numbers"
                style={{
                  fontSize: '16px',
                  fontWeight: 700,
                  marginTop: '4px',
                  color: data.peak_forecast_p90_pct >= 90 ? 'var(--color-crit-red)' : data.peak_forecast_p90_pct >= 80 ? 'var(--color-warn-amber)' : 'var(--color-safe-green)',
                }}
              >
                {data.peak_forecast_p90_pct}% at {String(data.peak_forecast_hour).padStart(2, '0')}:00
              </div>
              <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
                Threshold: Below 90% safe
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
