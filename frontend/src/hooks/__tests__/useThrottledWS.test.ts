/**
 * useThrottledWS hook tests
 */
import { renderHook, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useThrottledWS } from '@/hooks/useThrottledWS'

describe('useThrottledWS', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('returns null initially when latest is null', () => {
    const { result } = renderHook(() => useThrottledWS<string>(null))
    expect(result.current).toBeNull()
  })

  it('flushes the latest value after 1 second', async () => {
    const { result, rerender } = renderHook(
      ({ latest }) => useThrottledWS<number>(latest),
      { initialProps: { latest: null as number | null } }
    )
    expect(result.current).toBeNull()

    rerender({ latest: 42 })
    act(() => { vi.advanceTimersByTime(1000) })
    expect(result.current).toBe(42)
  })

  it('flushes only the latest of rapid updates', async () => {
    const { result, rerender } = renderHook(
      ({ latest }) => useThrottledWS<number>(latest),
      { initialProps: { latest: 1 as number | null } }
    )

    rerender({ latest: 2 })
    rerender({ latest: 3 })
    rerender({ latest: 99 })

    act(() => { vi.advanceTimersByTime(1000) })
    expect(result.current).toBe(99)
  })

  it('does not update again before 1 second passes', async () => {
    const { result, rerender } = renderHook(
      ({ latest }) => useThrottledWS<number>(latest),
      { initialProps: { latest: 1 as number | null } }
    )
    act(() => { vi.advanceTimersByTime(1000) })
    expect(result.current).toBe(1)

    rerender({ latest: 2 })
    act(() => { vi.advanceTimersByTime(500) }) // half second — no flush yet
    // After 1000ms from last flush, a new timer starts
    // so value should still be 1 until timer fires
    // (timer is started fresh so this checks no immediate update)
    expect(result.current).toBe(1)
  })
})
