/**
 * useThrottledWS — throttles WebSocket message renders to 1 per second.
 * Incoming messages are buffered; the latest value is flushed at most once/sec.
 * This prevents chart thrashing on high-frequency WS streams.
 *
 * Usage:
 *   const value = useThrottledWS<ClusterTick>(wsMessage)
 */
import { useEffect, useRef, useState } from 'react'

const THROTTLE_MS = 1000

export function useThrottledWS<T>(latest: T | null): T | null {
  const [flushed, setFlushed] = useState<T | null>(latest)
  const pendingRef = useRef<T | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (latest === null) return
    pendingRef.current = latest

    if (!timerRef.current) {
      timerRef.current = setTimeout(() => {
        setFlushed(pendingRef.current)
        timerRef.current = null
      }, THROTTLE_MS)
    }

    return () => {
      // Do NOT clear on every latest change — we want trailing edge flush
    }
  }, [latest])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [])

  return flushed
}
