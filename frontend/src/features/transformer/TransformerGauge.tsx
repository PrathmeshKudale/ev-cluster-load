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
  if (pct >= crit) return 'var(--color-crit-red)'
  if (pct >= warn) return 'var(--color-warn-amber)'
  return 'var(--color-safe-green)'
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
  const effectivePct = peakPct ?? data?.loading_percent ?? data?.current_load_pct ?? 0
  const effectiveKva = kva ?? data?.rating_kva
  const pct = Math.max(0, Math.min(100, effectivePct))
  const color = getSeverityColor(pct, warnThreshold, critThreshold)

  const option = useMemo(() => ({
    backgroundColor: 'transparent',
    animation: true,
    series: [
      {
        type: 'gauge',
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
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
              [warnThreshold / 100, 'var(--color-safe-green-bg)'],
              [critThreshold / 100, 'var(--color-warn-amber-bg)'],
              [1, 'var(--color-crit-red-bg)'],
            ],
          },
        },
        axisTick: { show: false },
        splitLine: {
          length: 10,
          lineStyle: { color: 'var(--color-border)', width: 2 },
        },
        axisLabel: {
          distance: 28,
          color: 'var(--color-text-muted)',
          fontSize: 12,
          formatter: '{value} %',
        },
        // Warning mark at warn threshold
        markPoint: undefined,
        pointer: {
          icon: 'path://M12.8,0.7l12.3,0L12.8,0.7z',
          length: '60%',
          width: 8,
          offsetCenter: [0, '5%'],
          itemStyle: { color: 'var(--color-text-secondary)' },
        },
        anchor: {
          show: true,
          showAbove: false,
          size: 20,
          itemStyle: {
            borderWidth: 3,
            borderColor: 'var(--color-text-secondary)',
            color: 'var(--color-surface)',
          },
        },
        title: {
          show: true,
          offsetCenter: [0, '-25%'],
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--color-text-secondary)',
        },
        detail: {
          valueAnimation: true,
          offsetCenter: [0, '10%'],
          fontSize: 32,
          fontWeight: 700,
          color,
          formatter: '{value} %',
          fontFamily: 'var(--font-mono)',
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
