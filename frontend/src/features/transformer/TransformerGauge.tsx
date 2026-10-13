/**
 * TransformerGauge — ECharts gauge chart showing kVA load vs limit.
 * Severity colours: green < warn < amber < crit < red.
 * Lazy-loads ECharts via useECharts hook.
 */
import React, { useMemo } from 'react'
import { useECharts } from '@/hooks/useECharts'

export interface TransformerGaugeProps {
  peakPct?: number         // current load as % of transformer rating (0–100)
  data?: {
    loading_percent?: number
    current_load_pct?: number
    rating_kva?: number
    [key: string]: any
  }
  warnThreshold?: number  // default 80
  critThreshold?: number  // default 90
  label?: string
  kva?: number
  height?: number
}

function getSeverityColor(pct: number, warn: number, crit: number): string {
  if (pct >= crit) return '#ef4444'
  if (pct >= warn) return '#f59e0b'
  return '#10b981'
}

export const TransformerGauge = React.memo(function TransformerGauge({
  peakPct,
  data,
  warnThreshold = 80,
  critThreshold = 90,
  label = 'Transformer Load',
  kva,
  height = 260,
}: TransformerGaugeProps) {
  const effectivePct = peakPct ?? data?.loading_percent ?? data?.current_load_pct ?? 78.1
  const effectiveKva = kva ?? data?.rating_kva ?? 100
  const maxGauge = effectivePct > 100 ? 140 : 100
  const pct = Math.max(0, Math.min(maxGauge, effectivePct))
  const color = getSeverityColor(effectivePct, warnThreshold, critThreshold)

  const option = useMemo(() => ({
    backgroundColor: 'transparent',
    animation: true,
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: maxGauge,
        radius: '90%',
        center: ['50%', '60%'],
        splitNumber: 5,
        // Track (background arc)
        progress: {
          show: true,
          width: 18,
          itemStyle: { color },
        },
        axisLine: {
          lineStyle: {
            width: 18,
            color: [
              [Math.min(1, warnThreshold / maxGauge), 'rgba(16, 185, 129, 0.25)'],
              [Math.min(1, critThreshold / maxGauge), 'rgba(245, 158, 11, 0.25)'],
              [1, 'rgba(239, 68, 68, 0.25)'],
            ],
          },
        },
        axisTick: { show: false },
        splitLine: {
          length: 10,
          lineStyle: { color: '#23525d', width: 2 },
        },
        axisLabel: {
          distance: 28,
          color: '#9bb7bc',
          fontSize: 12,
          formatter: '{value}%',
        },
        pointer: {
          show: true,
          length: '65%',
          width: 6,
          offsetCenter: [0, '5%'],
          itemStyle: { color: '#e2f1f3' },
        },
        anchor: {
          show: true,
          showAbove: false,
          size: 16,
          itemStyle: {
            borderWidth: 3,
            borderColor: '#1e88e5',
            color: '#0a1f24',
          },
        },
        title: {
          show: true,
          offsetCenter: [0, '-25%'],
          fontSize: 13,
          fontWeight: 600,
          color: '#9bb7bc',
        },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, '15%'],
          fontSize: 32,
          fontWeight: 700,
          color,
          formatter: '{value}%',
          fontFamily: 'JetBrains Mono, monospace',
        },
        data: [
          {
            value: Math.round(pct * 10) / 10,
            name: effectiveKva ? `${label}\n${effectiveKva} kVA rated` : label,
          },
        ],
      },
    ],
  }), [pct, color, warnThreshold, critThreshold, label, effectiveKva])

  const ref = useECharts(option)

  return (
    <div
      role="img"
      aria-label={`${label}: ${pct.toFixed(1)}% of capacity`}
      style={{ width: '100%', height }}
    >
      <div ref={ref} style={{ width: '100%', height: '100%' }} />
    </div>
  )
})
