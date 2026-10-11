/**
 * useWebSocket hook
 * Auto-reconnecting WebSocket with exponential backoff.
 * Pushes incoming 'cluster_telemetry' and 'forecast_update' messages
 * directly into the TanStack Query cache — no refetch needed.
 */
import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { patchForecastCache } from './queries'
import { useUIStore } from '../store/uiStore'

const WS_URL = (import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/api/v1/ws/live').replace(/\/$/, '')

const MAX_DELAY_MS = 30_000
const BASE_DELAY_MS = 500

interface WsMessage {
  type: string
  [key: string]: unknown
}

export function useWebSocket(enabled = true) {
  const qc = useQueryClient()
  const wsRef = useRef<WebSocket | null>(null)
  const retryCount = useRef(0)
  const retryTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const showToast = useUIStore((s) => s.showToast)
  const accessToken = useUIStore((s) => s.accessToken)

  const connect = useCallback(() => {
    if (!enabled) return
    const url = accessToken ? `${WS_URL}?token=${accessToken}` : WS_URL
    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      retryCount.current = 0
    }

    ws.onmessage = (evt) => {
      let msg: WsMessage
      try {
        msg = JSON.parse(evt.data)
      } catch {
        return
      }

      switch (msg.type) {
        case 'cluster_telemetry': {
          // Patch forecast cache p50/p90 with live values
          const patch = {
            ...(msg.p50_current != null && { p50: [msg.p50_current as number] }),
            ...(msg.p90_current != null && { p90: [msg.p90_current as number] }),
          }
          if (Object.keys(patch).length) {
            patchForecastCache(qc, patch)
          }
          break
        }
        case 'forecast_update': {
          patchForecastCache(qc, msg as Parameters<typeof patchForecastCache>[1])
          break
        }
        case 'alert': {
          showToast(String(msg.message ?? 'Grid alert received'), 'error')
          break
        }
        default:
          break
      }
    }

    ws.onerror = () => {
      ws.close()
    }

    ws.onclose = () => {
      wsRef.current = null
      const delay = Math.min(BASE_DELAY_MS * 2 ** retryCount.current, MAX_DELAY_MS)
      retryCount.current += 1
      retryTimer.current = setTimeout(connect, delay)
    }
  }, [enabled, qc, showToast, accessToken])

  useEffect(() => {
    connect()
    return () => {
      if (retryTimer.current) clearTimeout(retryTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  const send = useCallback((payload: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(payload))
    }
  }, [])

  return { send }
}
