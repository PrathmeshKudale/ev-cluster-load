/**
 * VirtualAlertFeed — virtualised alert feed using a simple windowing approach.
 * Renders only the visible rows (window of ITEM_HEIGHT × visible area).
 * Drop-in replacement for AlertFeed when the list can grow to 1000+ items.
 *
 * Uses a lightweight CSS-based virtual scroll (no extra dependencies).
 * Falls back to regular render when count < VIRTUAL_THRESHOLD.
 */
import React, { useRef, useState, useCallback, useMemo } from 'react'
import { AlertTriangle, AlertCircle, Info, CheckCircle2, Check } from 'lucide-react'
import type { AlertItem } from '@/fixtures/alertFixture'

const ITEM_HEIGHT = 72        // px per row (approximate)
const OVERSCAN    = 5         // extra rows rendered above/below viewport
const VIRTUAL_THRESHOLD = 50  // only virtualise when list exceeds this

function severityIcon(level: string) {
  if (level === 'critical') return <AlertCircle size={16} style={{ color: 'var(--color-crit-red)', flexShrink: 0 }} />
  if (level === 'warning')  return <AlertTriangle size={16} style={{ color: 'var(--color-warn-amber)', flexShrink: 0 }} />
  if (level === 'ok')       return <CheckCircle2 size={16} style={{ color: 'var(--color-safe-green)', flexShrink: 0 }} />
  return <Info size={16} style={{ color: 'var(--color-trafo-blue)', flexShrink: 0 }} />
}

function severityBg(level: string): React.CSSProperties {
  if (level === 'critical') return { borderLeft: '3px solid var(--color-crit-red)', background: 'var(--color-crit-red-bg)' }
  if (level === 'warning')  return { borderLeft: '3px solid var(--color-warn-amber)', background: 'var(--color-warn-amber-bg)' }
  return { borderLeft: '3px solid var(--color-border)' }
}

interface AlertRowProps {
  item: AlertItem
  onAck: (id: string) => void
  style?: React.CSSProperties
}

const AlertRow = React.memo(function AlertRow({ item, onAck, style }: AlertRowProps) {
  const lvl = item.level ?? (item.severity === 'crit' ? 'critical' : item.severity === 'warn' ? 'warning' : 'info')
  const entityId = item.station_id ?? item.entity_id ?? ''

  return (
    <div
      style={{
        ...style,
        display: 'flex',
        alignItems: 'flex-start',
        gap: '10px',
        padding: '10px 14px',
        marginBottom: '4px',
        borderRadius: 'var(--radius-sm)',
        opacity: item.acknowledged ? 0.55 : 1,
        ...severityBg(lvl),
      }}
      role="listitem"
      aria-label={`${lvl} alert: ${item.message}`}
    >
      {severityIcon(lvl)}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-primary)', lineHeight: 1.3 }}>
          {item.message}
        </div>
        <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>
          {entityId} · {new Date(item.timestamp).toLocaleTimeString()}
        </div>
      </div>
      {!item.acknowledged && (
        <button
          type="button"
          onClick={() => onAck(item.id)}
          aria-label={`Acknowledge alert: ${item.message}`}
          style={{
            flexShrink: 0,
            background: 'none',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px 6px',
            cursor: 'pointer',
            color: 'var(--color-text-secondary)',
            fontSize: '11px',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '3px',
          }}
        >
          <Check size={11} /> Ack
        </button>
      )}
    </div>
  )
})

export interface VirtualAlertFeedProps {
  alerts?: AlertItem[]
  onAcknowledge?: (id: string) => void
  maxVisible?: number   // viewport height in rows (default 8)
}

export const VirtualAlertFeed = React.memo(function VirtualAlertFeed({
  alerts = [],
  onAcknowledge,
  maxVisible = 8,
}: VirtualAlertFeedProps) {
  const [items, setItems] = useState<AlertItem[]>(alerts)
  const scrollRef = useRef<HTMLDivElement>(null)
  const [scrollTop, setScrollTop] = useState(0)

  const handleAck = useCallback((id: string) => {
    setItems(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a))
    onAcknowledge?.(id)
  }, [onAcknowledge])

  const containerHeight = maxVisible * ITEM_HEIGHT
  const totalHeight = items.length * ITEM_HEIGHT

  const onScroll = useCallback(() => {
    setScrollTop(scrollRef.current?.scrollTop ?? 0)
  }, [])

  // Visible window calculation
  const { startIdx, endIdx } = useMemo(() => {
    const start = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - OVERSCAN)
    const end = Math.min(items.length, Math.ceil((scrollTop + containerHeight) / ITEM_HEIGHT) + OVERSCAN)
    return { startIdx: start, endIdx: end }
  }, [scrollTop, containerHeight, items.length])

  // Skip virtualisation for small lists
  if (items.length < VIRTUAL_THRESHOLD) {
    return (
      <div
        role="list"
        aria-label="Alert feed"
        aria-live="polite"
        style={{ maxHeight: containerHeight, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}
      >
        {items.map(item => (
          <AlertRow key={item.id} item={item} onAck={handleAck} />
        ))}
        {items.length === 0 && (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--color-text-muted)', fontSize: '14px' }}>
            No alerts
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      ref={scrollRef}
      onScroll={onScroll}
      role="list"
      aria-label={`Alert feed — ${items.length} alerts`}
      aria-live="polite"
      style={{ height: containerHeight, overflowY: 'auto', position: 'relative' }}
    >
      {/* Spacer to create scroll room */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {items.slice(startIdx, endIdx).map((item, i) => (
          <AlertRow
            key={item.id}
            item={item}
            onAck={handleAck}
            style={{
              position: 'absolute',
              top: (startIdx + i) * ITEM_HEIGHT,
              left: 0,
              right: 0,
              height: ITEM_HEIGHT,
            }}
          />
        ))}
      </div>
    </div>
  )
})
