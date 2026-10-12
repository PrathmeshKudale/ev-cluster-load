export interface AlertItem {
  id: string
  timestamp: string
  severity?: 'info' | 'warn' | 'crit'
  level?: 'info' | 'warn' | 'crit' | 'critical' | 'warning' | 'ok' | string
  entity_type?: 'transformer' | 'station' | 'grid'
  entity_id?: string
  station_id?: string
  message: string
  action_label?: string
  acknowledged?: boolean
}

export const alertFixture: AlertItem[] = [
  {
    id: 'ALT-101',
    timestamp: '14:02 UTC',
    severity: 'crit',
    entity_type: 'station',
    entity_id: 'S4',
    message: 'Ring Road Hub (S4) all 4 plugs occupied. Queue waiting time exceeds 18 minutes.',
    action_label: 'Reroute Drivers',
    acknowledged: false,
  },
  {
    id: 'ALT-102',
    timestamp: '13:45 UTC',
    severity: 'warn',
    entity_type: 'transformer',
    entity_id: 'T1',
    message: 'P90 cluster load forecast crosses 80% warning threshold (86.5%) at 18:00 evening peak.',
    action_label: 'Review Headroom',
    acknowledged: false,
  },
  {
    id: 'ALT-103',
    timestamp: '12:00 UTC',
    severity: 'info',
    entity_type: 'grid',
    entity_id: 'ToD',
    message: 'Time-of-Day tariff transitioned to Solar Off-Peak (₹5.50 / kWh). Smart dispatch soaking excess solar.',
    action_label: 'Dismiss',
    acknowledged: true,
  },
  {
    id: 'ALT-104',
    timestamp: '11:15 UTC',
    severity: 'warn',
    entity_type: 'transformer',
    entity_id: 'T1',
    message: 'Substation ambient temperature reached 33.2°C. Thermal derating factor lowered to 0.978.',
    action_label: 'Acknowledge',
    acknowledged: true,
  },
]
