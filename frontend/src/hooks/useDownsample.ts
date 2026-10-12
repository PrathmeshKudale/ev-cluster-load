/**
 * useDownsample — LTTB (Largest-Triangle-Three-Buckets) downsampling hook.
 * Returns a memoised, downsampled copy of the data array capped at maxPoints.
 * Used for time-series charts to keep render cost bounded.
 */
import { useMemo } from 'react'

interface Point {
  x: number
  y: number
}

/** LTTB algorithm — O(n) approximation of Largest-Triangle-Three-Buckets. */
function lttb(data: Point[], threshold: number): Point[] {
  const n = data.length
  if (n <= threshold) return data

  const sampled: Point[] = [data[0]]
  const every = (n - 2) / (threshold - 2)

  let a = 0
  for (let i = 0; i < threshold - 2; i++) {
    const rangeStart = Math.floor((i + 1) * every) + 1
    const rangeEnd = Math.min(Math.floor((i + 2) * every) + 1, n - 1)

    // Average next bucket
    let avgX = 0, avgY = 0, avgRangeLength = 0
    for (let j = rangeStart; j < rangeEnd; j++) {
      avgX += data[j].x
      avgY += data[j].y
      avgRangeLength++
    }
    avgX /= avgRangeLength
    avgY /= avgRangeLength

    // Find point in current bucket that forms largest triangle
    const bucketStart = Math.floor(i * every) + 1
    const bucketEnd = Math.min(Math.floor((i + 1) * every) + 1, n - 1)

    const ax = data[a].x, ay = data[a].y
    let maxArea = -1, maxAreaPoint = data[bucketStart]

    for (let j = bucketStart; j < bucketEnd; j++) {
      const area = Math.abs(
        (ax - avgX) * (data[j].y - ay) - (ax - data[j].x) * (avgY - ay)
      ) * 0.5
      if (area > maxArea) {
        maxArea = area
        maxAreaPoint = data[j]
        a = j
      }
    }
    sampled.push(maxAreaPoint)
  }

  sampled.push(data[n - 1])
  return sampled
}

export function useDownsample(
  data: Point[],
  maxPoints = 500
): Point[] {
  return useMemo(() => lttb(data, maxPoints), [data, maxPoints])
}

/** Convenience: downsample parallel arrays (hours, values) */
export function useDownsampleSeries(
  xs: number[],
  ys: number[],
  maxPoints = 500
): { xs: number[]; ys: number[] } {
  return useMemo(() => {
    const points: Point[] = xs.map((x, i) => ({ x, y: ys[i] ?? 0 }))
    const sampled = lttb(points, maxPoints)
    return {
      xs: sampled.map(p => p.x),
      ys: sampled.map(p => p.y),
    }
  }, [xs, ys, maxPoints])
}
