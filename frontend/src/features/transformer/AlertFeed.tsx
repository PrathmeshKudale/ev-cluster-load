import React, { useState } from 'react'
import {
  Bell,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  Check,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { alertFixture, type AlertItem } from '@/fixtures/alertFixture'

export interface AlertFeedProps {
  alerts?: AlertItem[]
  onAcknowledge?: (alertId: string) => void
  onAction?: (alert: AlertItem) => void
  maxItems?: number
}

export const AlertFeed: React.FC<AlertFeedProps> = ({
  alerts = alertFixture,
  onAcknowledge,
  onAction,
  maxItems,
}) => {
  const [items, setItems] = useState<AlertItem[]>(alerts)
  const [filter, setFilter] = useState<'all' | 'active' | 'crit'>('all')

  const handleAck = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, acknowledged: true } : item))
    )
    onAcknowledge?.(id)
  }

  const handleActionClick = (item: AlertItem, e: React.MouseEvent) => {
    e.stopPropagation()
    onAction?.(item)
  }

  const filteredItems = items
    .filter((item) => {
      if (filter === 'active') return !item.acknowledged
      if (filter === 'crit') return item.severity === 'crit'
      return true
    })
    .slice(0, maxItems ?? items.length)

  const activeCount = items.filter((i) => !i.acknowledged).length
  const critCount = items.filter((i) => i.severity === 'crit' && !i.acknowledged).length

  return (
    <Card style={{ width: '100%' }}>
      <CardHeader>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              position: 'relative',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Bell size={20} color="var(--color-trafo-blue)" />
            {activeCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '-4px',
                  right: '-4px',
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: critCount > 0 ? 'var(--color-crit-red)' : 'var(--color-warn-amber)',
                }}
              />
            )}
          </div>
          <div>
            <CardTitle>Live Grid Alert Feed</CardTitle>
            <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
              Substation Thresholds & Congestion Stream ({activeCount} Active)
            </p>
          </div>
        </div>

        {/* Filter Tabs */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <Button
            size="sm"
            variant={filter === 'all' ? 'secondary' : 'ghost'}
            onClick={() => setFilter('all')}
          >
            All ({items.length})
          </Button>
          <Button
            size="sm"
            variant={filter === 'active' ? 'secondary' : 'ghost'}
            onClick={() => setFilter('active')}
          >
            Active ({activeCount})
          </Button>
          <Button
            size="sm"
            variant={filter === 'crit' ? 'danger' : 'ghost'}
            onClick={() => setFilter('crit')}
          >
            Critical ({critCount})
          </Button>
        </div>
      </CardHeader>

      <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {filteredItems.length === 0 ? (
          <div
            style={{
              padding: '32px 16px',
              textAlign: 'center',
              color: 'var(--color-ink-300)',
              fontSize: '14px',
              background: 'var(--color-ink-850)',
              borderRadius: '8px',
            }}
          >
            <CheckCircle2 size={32} color="var(--color-safe-green)" style={{ margin: '0 auto 8px' }} />
            <p style={{ fontWeight: 600, color: 'var(--color-ink-100)' }}>All Systems Clear</p>
            <p style={{ fontSize: '12px' }}>No active alerts matching the selected filter.</p>
          </div>
        ) : (
          filteredItems.map((item) => {
            const isCrit = item.severity === 'crit'
            const isWarn = item.severity === 'warn'
            const isAck = item.acknowledged

            const borderLeftColor = isCrit
              ? 'var(--color-crit-red)'
              : isWarn
              ? 'var(--color-warn-amber)'
              : 'var(--color-trafo-blue)'

            const bgTint = isAck
              ? 'var(--color-ink-850)'
              : isCrit
              ? 'rgba(220, 38, 38, 0.08)'
              : isWarn
              ? 'rgba(217, 119, 6, 0.08)'
              : 'var(--color-ink-850)'

            return (
              <div
                key={item.id}
                role="article"
                aria-label={`${item.severity} alert: ${item.message}`}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '12px',
                  padding: '12px 14px',
                  background: bgTint,
                  border: '1px solid var(--color-ink-700)',
                  borderLeft: `4px solid ${borderLeftColor}`,
                  borderRadius: '6px',
                  opacity: isAck ? 0.65 : 1,
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ display: 'flex', gap: '12px', flex: 1, minWidth: 0 }}>
                  <div style={{ marginTop: '2px', flexShrink: 0 }}>
                    {isCrit ? (
                      <AlertCircle size={18} color="var(--color-crit-red)" />
                    ) : isWarn ? (
                      <AlertTriangle size={18} color="var(--color-warn-amber)" />
                    ) : (
                      <Info size={18} color="var(--color-trafo-blue)" />
                    )}
                  </div>

                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        flexWrap: 'wrap',
                        marginBottom: '4px',
                      }}
                    >
                      <Badge
                        variant={isCrit ? 'crit' : isWarn ? 'warn' : 'brand'}
                        style={{ fontSize: '10px', padding: '2px 6px' }}
                      >
                        {(item.entity_type ?? 'ALERT').toUpperCase()} • {item.entity_id ?? item.id}
                      </Badge>

                      <span
                        style={{
                          fontSize: '11px',
                          color: 'var(--color-ink-400)',
                          fontFamily: 'var(--font-mono)',
                        }}
                      >
                        {item.timestamp}
                      </span>

                      {isAck && (
                        <span
                          style={{
                            fontSize: '11px',
                            color: 'var(--color-safe-green)',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '3px',
                          }}
                        >
                          <Check size={11} /> Acked
                        </span>
                      )}
                    </div>

                    <p
                      style={{
                        margin: 0,
                        fontSize: '13px',
                        lineHeight: 1.4,
                        color: isAck ? 'var(--color-ink-300)' : 'var(--color-ink-100)',
                      }}
                    >
                      {item.message}
                    </p>
                  </div>
                </div>

                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    flexShrink: 0,
                  }}
                >
                  {item.action_label && !isAck && (
                    <Button
                      size="sm"
                      variant={isCrit ? 'danger' : 'outline'}
                      onClick={(e) => handleActionClick(item, e)}
                      style={{ fontSize: '11px', height: '28px', padding: '0 8px' }}
                    >
                      {item.action_label}
                    </Button>
                  )}

                  {!isAck ? (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={(e) => handleAck(item.id, e)}
                      aria-label={`Acknowledge alert ${item.id}`}
                      style={{
                        fontSize: '11px',
                        height: '28px',
                        padding: '0 8px',
                        color: 'var(--color-ink-300)',
                      }}
                    >
                      Dismiss
                    </Button>
                  ) : null}
                </div>
              </div>
            )
          })
        )}
      </CardContent>
    </Card>
  )
}
export default AlertFeed
