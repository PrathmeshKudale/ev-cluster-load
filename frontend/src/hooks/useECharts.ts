/**
 * useECharts — lazy-loads ECharts core + only the charts/components used.
 * Respects prefers-reduced-motion (disables animation).
 * Memo-safe: option reference stability is checked via JSON hash before setOption.
 */
import { useEffect, useRef, useCallback } from 'react'

export type EChartsOption = Record<string, unknown>

// Stable hash to skip redundant setOption calls
function jsonHash(obj: unknown): string {
  try { return JSON.stringify(obj) } catch { return String(obj) }
}

const prefersReducedMotion =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

export function useECharts(option: EChartsOption | null) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<unknown>(null)
  const lastHashRef = useRef<string>('')

  // Lazy init
  const initChart = useCallback(async () => {
    if (!containerRef.current || chartRef.current) return

    const echarts = await import('echarts/core')
    const { LineChart, GaugeChart, BarChart } = await import('echarts/charts')
    const {
      GridComponent,
      TooltipComponent,
      MarkLineComponent,
      MarkAreaComponent,
      LegendComponent,
    } = await import('echarts/components')
    const { CanvasRenderer } = await import('echarts/renderers')

    echarts.use([
      LineChart, GaugeChart, BarChart,
      GridComponent, TooltipComponent, MarkLineComponent,
      MarkAreaComponent, LegendComponent,
      CanvasRenderer,
    ])

    chartRef.current = echarts.init(containerRef.current, null, {
      renderer: 'canvas',
      useDirtyRect: true,
    })
  }, [])

  // Apply option
  useEffect(() => {
    if (!option) return
    const hash = jsonHash(option)

    const apply = async () => {
      await initChart()
      if (!chartRef.current || hash === lastHashRef.current) return
      lastHashRef.current = hash
      const optWithMotion = prefersReducedMotion
        ? { ...option, animation: false }
        : option
      ;(chartRef.current as { setOption: (o: unknown) => void }).setOption(
        optWithMotion,
        { notMerge: false, lazyUpdate: true }
      )
    }
    apply()
  }, [option, initChart])

  // Resize observer
  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const ro = new ResizeObserver(() => {
      if (chartRef.current) {
        (chartRef.current as { resize: () => void }).resize()
      }
    })
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (chartRef.current) {
        (chartRef.current as { dispose: () => void }).dispose()
        chartRef.current = null
      }
    }
  }, [])

  return containerRef
}
