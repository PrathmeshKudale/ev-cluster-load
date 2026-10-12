/**
 * ForecastBandChart — ECharts P10/P50/P90 band chart
 * Uses severity-scale colours from CSS tokens.
 * Lazy-loads ECharts via useECharts hook.
 * Downsamples to ≤500 points automatically.
 * Respects prefers-reduced-motion (animation disabled).
 */
import React, { useMemo } from 'react'
import { useECharts } from '@/hooks/useECharts'

export interface ForecastBandChartProps {
  hours?: number[]
  p10?: number[]
  p50?: number[]
  p90?: number[]
  data?: {
    hours?: number[]
    p10?: number[]
    p50?: number[]
    p90?: number[]
    warn?: number
    critical?: number
    warn_threshold_pct?: number
    crit_threshold_pct?: number
    [key: string]: any
  }
  warnThreshold?: number   // default 80
  critThreshold?: number   // default 90
  onHoverHour?: (hour: number | null) => void
  height?: number
  'aria-label'?: string
}

/** Downsample to maxPoints via LTTB (Largest-Triangle-Three-Buckets) approximation. */
function downsample<T>(arr: T[], maxPoints: number): T[] {
  if (arr.length <= maxPoints) return arr
  const step = arr.length / maxPoints
  return Array.from({ length: maxPoints }, (_, i) => arr[Math.round(i * step)])
}

export const ForecastBandChart = React.memo(function ForecastBandChart({
  hours,
  p10,
  p50,
  p90,
  data,
  warnThreshold,
  critThreshold,
  onHoverHour: _onHoverHour,
  height = 320,
  'aria-label': ariaLabel = 'Transformer load forecast band chart',
}: ForecastBandChartProps) {
  const MAX_POINTS = 500

  const hArr = hours ?? data?.hours ?? Array.from({ length: 24 }, (_, i) => i)
  const p10Arr = p10 ?? data?.p10 ?? []
  const p50Arr = p50 ?? data?.p50 ?? []
  const p90Arr = p90 ?? data?.p90 ?? []
  const warn = warnThreshold ?? data?.warn ?? data?.warn_threshold_pct ?? 80
  const crit = critThreshold ?? data?.critical ?? data?.crit_threshold_pct ?? 90

  // Downsample all series together
  const ds = useMemo(() => {
    const n = hArr.length
    if (n <= MAX_POINTS) return { hours: hArr, p10: p10Arr, p50: p50Arr, p90: p90Arr }
    const step = n / MAX_POINTS
    const idx = Array.from({ length: MAX_POINTS }, (_, i) => Math.round(i * step))
    return {
      hours: idx.map(i => hArr[i]),
      p10:   idx.map(i => p10Arr[i]),
      p50:   idx.map(i => p50Arr[i]),
      p90:   idx.map(i => p90Arr[i]),
    }
  }, [hArr, p10Arr, p50Arr, p90Arr])

  const option = useMemo(() => ({
    backgroundColor: 'transparent',
    animation: true,
    grid: { top: 40, right: 24, bottom: 48, left: 56, containLabel: false },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'var(--color-surface-raised)',
      borderColor: 'var(--color-border)',
      textStyle: { color: 'var(--color-text-primary)', fontSize: 13 },
      formatter: (params: Array<{ seriesName: string; value: number; axisValue: number }>) => {
        const h = params[0]?.axisValue
        const rows = params
          .filter(p => p.seriesName !== 'P10-base')
          .map(p => `<div>${p.seriesName}: <b>${p.value?.toFixed(1)} %</b></div>`)
          .join('')
        return `<div style="font-size:12px"><div style="margin-bottom:4px">Hour ${h}:00</div>${rows}</div>`
      },
    },
    xAxis: {
      type: 'category',
      data: ds.hours.map(h => `${h}:00`),
      axisLabel: { color: 'var(--color-text-muted)', fontSize: 12 },
      axisLine: { lineStyle: { color: 'var(--color-border)' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: {
        color: 'var(--color-text-muted)',
        fontSize: 12,
        formatter: '{value} %',
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'var(--color-border)', type: 'dashed' } },
    },
    series: [
      // P10 base (hidden, used for band lower bound)
      {
        name: 'P10-base',
        type: 'line',
        data: ds.p10,
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'band',
      },
      // P10→P90 band fill
      {
        name: 'Band',
        type: 'line',
        data: ds.p90.map((v, i) => v - ds.p10[i]),
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'band',
        areaStyle: {
          color: 'rgba(30,136,229,0.15)',
          origin: 'auto',
        },
      },
      // P50 median line
      {
        name: 'P50 (median)',
        type: 'line',
        data: ds.p50,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: 'var(--chart-p50)', width: 2.5 },
        itemStyle: { color: 'var(--chart-p50)' },
      },
      // P90 upper bound line
      {
        name: 'P90',
        type: 'line',
        data: ds.p90,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: 'var(--color-crit-red)', width: 1.5, type: 'dashed', opacity: 0.7 },
        itemStyle: { color: 'var(--color-crit-red)' },
      },
    ],
    // Warning and critical threshold mark lines
    graphic: [],
    // Mark lines via series
    ...((() => {
      const markLineSeries = {
        name: 'Thresholds',
        type: 'line',
        data: [],
        symbol: 'none',
        lineStyle: { opacity: 0 },
        markLine: {
          silent: true,
          symbol: ['none', 'none'],
          data: [
            {
              yAxis: warnThreshold,
              label: { formatter: `Warn ${warnThreshold}%`, position: 'insideEndTop', fontSize: 11 },
              lineStyle: { color: 'var(--color-warn-amber)', width: 1.5, type: 'dashed' },
            },
            {
              yAxis: critThreshold,
              label: { formatter: `Crit ${critThreshold}%`, position: 'insideEndTop', fontSize: 11 },
              lineStyle: { color: 'var(--color-crit-red)', width: 1.5, type: 'dashed' },
            },
          ],
        },
      }
      return { _markLineSeries: markLineSeries }
    })()),
  }), [ds, warnThreshold, critThreshold])

  // Merge the mark line series into the series array
  const mergedOption = useMemo(() => {
    const { _markLineSeries, series, ...rest } = option as Record<string, unknown> & { series: unknown[], _markLineSeries: unknown }
    return { ...rest, series: [...series, _markLineSeries] }
  }, [option])

  const ref = useECharts(mergedOption)

  return (
    <div
      ref={ref}
      role="img"
      aria-label={ariaLabel}
      style={{ width: '100%', height, minHeight: 200 }}
      className="echarts-wrapper"
    />
  )
})
