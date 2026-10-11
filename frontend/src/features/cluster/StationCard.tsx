import React from 'react'
import { BatteryCharging, Clock, Navigation, CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { stationsFixture, type StationDetailFixture } from '@/fixtures/stationsFixture'

export interface StationCardProps {
  station?: StationDetailFixture
  onSelect?: (stationId: string) => void
  selected?: boolean
}

export const StationCard: React.FC<StationCardProps> = ({
  station = stationsFixture[0],
  onSelect,
  selected = false,
}) => {
  const availableCount = station.chargers.filter((c) => c.status === 'Available').length
  const isFull = availableCount === 0
  const isBusy = station.utilization_percent >= 80

  const statusVariant = isFull ? 'crit' : isBusy ? 'warn' : 'normal'
  const statusLabel = isFull ? 'ALL FULL' : isBusy ? 'HIGH QUEUE' : `${availableCount} FREE`

  return (
    <Card
      elevated={selected}
      severity={isFull ? 'crit' : isBusy ? 'warn' : 'normal'}
      style={{
        borderWidth: selected ? '2px' : '1px',
        borderColor: selected ? 'var(--color-trafo-blue)' : undefined,
      }}
    >
      <CardHeader>
        <div>
          <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{station.name}</span>
            <span style={{ fontSize: '12px', color: 'var(--color-ink-300)', fontWeight: 500 }}>
              ({station.id})
            </span>
          </CardTitle>
          <div style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
            {station.chargers_count} Plugs • {station.kw_per_charger} kW Type 2 AC
          </div>
        </div>
        <Badge
          variant={statusVariant}
          icon={
            isFull ? (
              <AlertCircle size={12} />
            ) : isBusy ? (
              <AlertTriangle size={12} />
            ) : (
              <CheckCircle2 size={12} />
            )
          }
        >
          {statusLabel}
        </Badge>
      </CardHeader>

      <CardContent>
        {/* Real-time Utilization Bar */}
        <div style={{ marginBottom: '14px' }}>
          <Progress
            value={station.utilization_percent}
            showLabel
            label={`Occupancy (${station.active_sessions}/${station.chargers_count} in use)`}
          />
        </div>

        {/* Operational Metrics Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '8px',
            backgroundColor: 'var(--color-ink-900)',
            padding: '10px 12px',
            borderRadius: 'var(--radius-sm)',
            marginBottom: '14px',
          }}
        >
          <div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)' }}>Erlang-C Wait</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: station.erlang_c_wait_min > 10 ? 'var(--color-crit-red)' : 'var(--color-ink-100)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '2px',
              }}
            >
              <Clock size={14} color="var(--color-ink-300)" />
              {station.erlang_c_wait_min.toFixed(1)} m
            </div>
          </div>

          <div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)' }}>Detour Time</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: 'var(--color-ink-100)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '2px',
              }}
            >
              <Navigation size={14} color="var(--color-ink-300)" />
              +{station.detour_min} m
            </div>
          </div>

          <div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)' }}>Active Power</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: 'var(--color-ink-100)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '2px',
              }}
            >
              <BatteryCharging size={14} color="var(--color-trafo-blue)" />
              {station.current_active_kw} kW
            </div>
          </div>
        </div>

        {/* Individual Bay Plugs Pills */}
        <div style={{ marginBottom: '14px' }}>
          <div style={{ fontSize: '12px', color: 'var(--color-ink-300)', marginBottom: '6px' }}>
            Live Bay Status
          </div>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {station.chargers.map((ch) => {
              const isChCharging = ch.status === 'Charging'
              return (
                <div
                  key={ch.id}
                  style={{
                    padding: '4px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontFamily: 'var(--font-mono)',
                    backgroundColor: isChCharging ? 'var(--color-trafo-blue-tint)' : 'var(--color-safe-green-bg)',
                    color: isChCharging ? 'var(--color-trafo-blue)' : 'var(--color-safe-green)',
                    border: `1px solid ${isChCharging ? 'var(--color-trafo-blue)' : 'var(--color-safe-green)'}`,
                  }}
                >
                  #{ch.evse_id}: {ch.status.toUpperCase()}
                </div>
              )
            })}
          </div>
        </div>

        {/* Selection Button */}
        <Button
          variant={selected ? 'primary' : 'outline'}
          size="sm"
          style={{ width: '100%' }}
          onClick={() => onSelect?.(station.id)}
        >
          {selected ? 'Station Selected' : 'Select Station'}
        </Button>
      </CardContent>
    </Card>
  )
}
