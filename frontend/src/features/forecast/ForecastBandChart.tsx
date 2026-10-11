import React, { useState } from 'react'
import { TrendingUp, AlertTriangle, ShieldAlert, Clock, Sparkles } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { forecastFixture, type ForecastFixture } from '@/fixtures/forecastFixture'

export interface ForecastBandChartProps {
  data?: ForecastFixture
  onHoverHour?: (hour: number) => void
}

export const ForecastBandChart: React.FC<ForecastBandChartProps> = ({
  data = forecastFixture,
  onHoverHour,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)

  // Chart dimensions & coordinates
  const W = 960
  const H = 340
  const padLeft = 50
  const padRight = 80
  const padTop = 20
  const padBottom = 60
  const maxScale = 110 // Max Y value in percentage

  const getX = (i: number) => padLeft + (i * (W - padLeft - padRight)) / (data.hours.length - 1)
  const getY = (val: number) => padTop + (1 - Math.min(val, maxScale) / maxScale) * (H - padTop - padBottom)

  const handlePointer = (idx: number) => {
    setHoverIndex(idx)
    onHoverHour?.(data.hours[idx])
  }

  // Construct SVG polygon points for P10 -> P90 band
  const p90Coords = data.p90.map((v, i) => `${getX(i)},${getY(v)}`)
  const p10Coords = data.p10.map((v, i) => `${getX(i)},${getY(v)}`).reverse()
  const bandPoints = [...p90Coords, ...p10Coords].join(' ')

  // Construct SVG polylines
  const p50Polyline = data.p50.map((v, i) => `${getX(i)},${getY(v)}`).join(' ')
  const p90Polyline = data.p90.map((v, i) => `${getX(i)},${getY(v)}`).join(' ')
  const p10Polyline = data.p10.map((v, i) => `${getX(i)},${getY(v)}`).join(' ')

  const activeIdx = hoverIndex !== null ? hoverIndex : data.hours.indexOf(data.peak_hour)
  const activeHour = data.hours[activeIdx] ?? data.hours[0]
  const activeP10 = data.p10[activeIdx] ?? 0
  const activeP50 = data.p50[activeIdx] ?? 0
  const activeP90 = data.p90[activeIdx] ?? 0

  return (
    <Card style={{ width: '100%' }}>
      <CardHeader>
        <div>
          <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={20} color="var(--color-trafo-blue)" />
            <span>24-Hour Calibrated Quantile Forecast</span>
          </CardTitle>
          <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
            LightGBM Conformal Quantiles • P10, P50 (Expected), and P90 (Worst-Case) Load
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <Badge variant="warn" icon={<AlertTriangle size={12} />}>
            Warn Limit: 80%
          </Badge>
          <Badge variant="crit" icon={<ShieldAlert size={12} />}>
            Critical Limit: 90%
          </Badge>
          <Badge variant="brand" icon={<Sparkles size={12} />}>
            Coverage: 81.2%
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* SVG Forecast Chart */}
        <div
          style={{
            position: 'relative',
            backgroundColor: 'var(--color-ink-950)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-ink-700)',
            padding: '12px 0 4px',
          }}
        >
          <svg
            viewBox={`0 0 ${W} ${H}`}
            style={{ width: '100%', height: 'auto', display: 'block' }}
            role="img"
            aria-label="24-hour calibrated quantile cluster load forecast chart"
          >
            {/* Background shading for hours exceeding 80% or 90% */}
            {data.hours.map((_, i) => {
              if (i === data.hours.length - 1) return null
              const p90Val = data.p90[i]
              if (p90Val < 80) return null
              const isCrit = p90Val >= 90
              const x1 = getX(i)
              const x2 = getX(i + 1)
              return (
                <rect
                  key={`exceed-bg-${i}`}
                  x={x1}
                  y={padTop}
                  width={x2 - x1}
                  height={H - padTop - padBottom}
                  fill={isCrit ? 'var(--color-crit-red)' : 'var(--color-warn-amber)'}
                  opacity={isCrit ? 0.16 : 0.10}
                />
              )
            })}

            {/* Horizontal Grid Lines */}
            {[0, 20, 40, 60, 80, 90, 100].map((val) => {
              const yPos = getY(val)
              const isWarn = val === 80
              const isCrit = val === 90
              return (
                <g key={`grid-y-${val}`}>
                  <line
                    x1={padLeft}
                    y1={yPos}
                    x2={W - padRight}
                    y2={yPos}
                    stroke={
                      isCrit
                        ? 'var(--color-crit-red)'
                        : isWarn
                        ? 'var(--color-warn-amber)'
                        : 'var(--color-ink-750)'
                    }
                    strokeWidth={isCrit || isWarn ? 1.5 : 0.8}
                    strokeDasharray={isCrit || isWarn ? '5 3' : undefined}
                  />
                  <text
                    x={padLeft - 8}
                    y={yPos + 4}
                    textAnchor="end"
                    fill={
                      isCrit
                        ? 'var(--color-crit-red)'
                        : isWarn
                        ? 'var(--color-warn-amber)'
                        : 'var(--color-ink-400)'
                    }
                    fontSize="11"
                    fontWeight={isCrit || isWarn ? 700 : 400}
                    fontFamily="var(--font-mono)"
                  >
                    {val}%
                  </text>
                  {(isWarn || isCrit) && (
                    <text
                      x={W - padRight + 8}
                      y={yPos + 4}
                      fill={isCrit ? 'var(--color-crit-red)' : 'var(--color-warn-amber)'}
                      fontSize="10"
                      fontWeight={700}
                      fontFamily="var(--font-sans)"
                    >
                      {isCrit ? '90% CRIT' : '80% WARN'}
                    </text>
                  )}
                </g>
              )
            })}

            {/* P10 - P90 Shaded Uncertainty Band */}
            <polygon
              points={bandPoints}
              fill="var(--color-trafo-blue)"
              opacity="0.22"
            />

            {/* P10 Dotted Line (Optimistic) */}
            <polyline
              points={p10Polyline}
              fill="none"
              stroke="var(--color-trafo-blue)"
              strokeWidth="1.5"
              strokeDasharray="2 3"
              opacity="0.7"
            />

            {/* P90 Dashed Line (Worst-case) */}
            <polyline
              points={p90Polyline}
              fill="none"
              stroke="var(--color-warn-amber)"
              strokeWidth="2"
              strokeDasharray="6 3"
            />

            {/* P50 Solid Line (Expected) */}
            <polyline
              points={p50Polyline}
              fill="none"
              stroke="var(--color-trafo-blue)"
              strokeWidth="3"
            />

            {/* X-axis Hour Labels */}
            {data.hours.map((h, i) => {
              const xPos = getX(i)
              const isTick = i % 2 === 0
              return (
                <g key={`x-tick-${i}`}>
                  {isTick && (
                    <text
                      x={xPos}
                      y={H - padBottom + 18}
                      textAnchor="middle"
                      fill={h === data.peak_hour ? 'var(--color-warn-amber)' : 'var(--color-ink-300)'}
                      fontSize="11"
                      fontWeight={h === data.peak_hour ? 700 : 400}
                      fontFamily="var(--font-mono)"
                    >
                      {String(h).padStart(2, '0')}:00
                    </text>
                  )}
                </g>
              )
            })}

            {/* ToD Tariff Color Ribbons along the bottom */}
            {data.hours.map((h, i) => {
              if (i === data.hours.length - 1) return null
              const isPeak = h >= 17 && h < 23
              const isSolar = h >= 9 && h < 17
              const ribbonColor = isPeak
                ? 'var(--color-crit-red)'
                : isSolar
                ? 'var(--color-safe-green)'
                : 'var(--color-trafo-blue)'
              const x1 = getX(i)
              const x2 = getX(i + 1)
              return (
                <rect
                  key={`tod-bar-${i}`}
                  x={x1}
                  y={H - padBottom + 28}
                  width={x2 - x1}
                  height="6"
                  fill={ribbonColor}
                  opacity="0.8"
                />
              )
            })}

            {/* Interactive Vertical Cursor Indicator */}
            {activeIdx !== null && (
              <g>
                <line
                  x1={getX(activeIdx)}
                  y1={padTop}
                  x2={getX(activeIdx)}
                  y2={H - padBottom}
                  stroke="var(--color-ink-100)"
                  strokeWidth="1.5"
                  strokeDasharray="3 3"
                />
                <circle
                  cx={getX(activeIdx)}
                  cy={getY(data.p50[activeIdx])}
                  r="5"
                  fill="var(--color-trafo-blue)"
                  stroke="#ffffff"
                  strokeWidth="2"
                />
                <circle
                  cx={getX(activeIdx)}
                  cy={getY(data.p90[activeIdx])}
                  r="4"
                  fill="var(--color-warn-amber)"
                  stroke="#ffffff"
                  strokeWidth="1.5"
                />
              </g>
            )}

            {/* Invisible transparent rects for hover hit-testing */}
            {data.hours.map((_, i) => {
              const xPos = getX(i) - 15
              return (
                <rect
                  key={`hitbox-${i}`}
                  x={xPos}
                  y={padTop}
                  width="30"
                  height={H - padTop}
                  fill="transparent"
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => handlePointer(i)}
                  onTouchStart={() => handlePointer(i)}
                />
              )
            })}
          </svg>
        </div>

        {/* Legend and Active Point Callout */}
        <div
          style={{
            marginTop: '14px',
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            fontSize: '13px',
          }}
        >
          {/* Legend Items */}
          <div style={{ display: 'flex', gap: '18px', alignItems: 'center', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div style={{ width: '18px', height: '3px', backgroundColor: 'var(--color-trafo-blue)' }} />
              <span style={{ color: 'var(--color-ink-100)' }}>P50 Expected (Solid)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div
                style={{
                  width: '18px',
                  height: '3px',
                  backgroundColor: 'var(--color-warn-amber)',
                  borderTop: '2px dashed var(--color-warn-amber)',
                }}
              />
              <span style={{ color: 'var(--color-ink-100)' }}>P90 Worst-Case (Dashed)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div
                style={{
                  width: '18px',
                  height: '3px',
                  borderTop: '2px dotted var(--color-trafo-blue)',
                }}
              />
              <span style={{ color: 'var(--color-ink-100)' }}>P10 Optimistic (Dotted)</span>
            </div>
          </div>

          {/* Active Hover Inspection Badge */}
          <div
            style={{
              padding: '6px 12px',
              backgroundColor: 'var(--color-ink-850)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-ink-700)',
              display: 'flex',
              gap: '12px',
              alignItems: 'center',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--color-ink-300)' }}>
              <Clock size={14} />
              <span>{String(activeHour).padStart(2, '0')}:00 UTC</span>
            </div>
            <span style={{ color: 'var(--color-trafo-blue)' }}>P50: {activeP50.toFixed(1)}%</span>
            <span
              style={{
                color: activeP90 >= 90 ? 'var(--color-crit-red)' : activeP90 >= 80 ? 'var(--color-warn-amber)' : 'var(--color-ink-100)',
                fontWeight: 700,
              }}
            >
              P90: {activeP90.toFixed(1)}%
            </span>
            <span style={{ color: 'var(--color-ink-300)' }}>P10: {activeP10.toFixed(1)}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
