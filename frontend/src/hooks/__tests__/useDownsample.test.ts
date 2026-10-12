/**
 * useDownsample hook tests
 */
import { renderHook } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { useDownsample, useDownsampleSeries } from '@/hooks/useDownsample'

describe('useDownsample', () => {
  it('returns original data when length <= maxPoints', () => {
    const data = Array.from({ length: 100 }, (_, i) => ({ x: i, y: Math.sin(i) }))
    const { result } = renderHook(() => useDownsample(data, 500))
    expect(result.current).toHaveLength(100)
  })

  it('downsamples to maxPoints when data exceeds threshold', () => {
    const data = Array.from({ length: 1000 }, (_, i) => ({ x: i, y: Math.sin(i * 0.1) }))
    const { result } = renderHook(() => useDownsample(data, 500))
    expect(result.current.length).toBeLessThanOrEqual(500)
  })

  it('preserves first and last points', () => {
    const data = Array.from({ length: 800 }, (_, i) => ({ x: i, y: i }))
    const { result } = renderHook(() => useDownsample(data, 100))
    expect(result.current[0]).toEqual(data[0])
    expect(result.current[result.current.length - 1]).toEqual(data[data.length - 1])
  })

  it('handles empty array', () => {
    const { result } = renderHook(() => useDownsample([], 500))
    expect(result.current).toHaveLength(0)
  })
})

describe('useDownsampleSeries', () => {
  it('returns correctly typed xs/ys', () => {
    const xs = Array.from({ length: 1000 }, (_, i) => i)
    const ys = Array.from({ length: 1000 }, (_, i) => Math.sin(i))
    const { result } = renderHook(() => useDownsampleSeries(xs, ys, 500))
    expect(result.current.xs.length).toBeLessThanOrEqual(500)
    expect(result.current.xs.length).toEqual(result.current.ys.length)
  })
})
