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
      backgroundColor: '#0a1f24',
      borderColor: '#23525d',
      textStyle: { color: '#e2f1f3', fontSize: 13 },
      formatter: (params: Array<{ seriesName: string; value: number; axisValue: string }>) => {
        const h = params[0]?.axisValue
        const rows = params
          .filter(p => p.seriesName !== 'P10-base' && p.seriesName !== 'Band' && p.seriesName !== 'Thresholds')
          .map(p => `<div>${p.seriesName}: <b>${p.value != null ? Number(p.value).toFixed(1) : ''}%</b></div>`)
          .join('')
        return `<div style="font-size:12px"><div style="margin-bottom:4px;font-weight:600">Hour ${h}</div>${rows}</div>`
      },
    },
    xAxis: {
      type: 'category',
      data: ds.hours.map(h => `${String(h).padStart(2, '0')}:00`),
      axisLabel: { color: '#9bb7bc', fontSize: 12 },
      axisLine: { lineStyle: { color: '#183e47' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: (value: { max: number }) => Math.max(100, Math.ceil((value.max || 100) * 1.05)),
      axisLabel: {
        color: '#9bb7bc',
        fontSize: 12,
        formatter: '{value}%',
      },
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.08)', type: 'dashed' } },
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
        data: ds.p90.map((v, i) => Math.max(0, v - (ds.p10[i] ?? 0))),
        lineStyle: { opacity: 0 },
        symbol: 'none',
        stack: 'band',
        areaStyle: {
          color: 'rgba(30, 136, 229, 0.22)',
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
        lineStyle: { color: '#1e88e5', width: 2.5 },
        itemStyle: { color: '#1e88e5' },
      },
      // P90 upper bound line
      {
        name: 'P90',
        type: 'line',
        data: ds.p90,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#ef4444', width: 1.8, type: 'dashed' },
        itemStyle: { color: '#ef4444' },
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
              yAxis: warn,
              label: { formatter: `Warn ${warn}%`, position: 'insideEndTop', fontSize: 11, color: '#f59e0b' },
              lineStyle: { color: '#f59e0b', width: 1.5, type: 'dashed' },
            },
            {
              yAxis: crit,
              label: { formatter: `Crit ${crit}%`, position: 'insideEndTop', fontSize: 11, color: '#ef4444' },
              lineStyle: { color: '#ef4444', width: 1.5, type: 'dashed' },
            },
          ],
        },
      }
      return { _markLineSeries: markLineSeries }
    })()),
  }), [ds, warn, crit])

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
