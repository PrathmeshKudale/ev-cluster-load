import React from 'react'

export interface ProgressProps {
  value: number // 0 to 100
  max?: number
  warnThreshold?: number // e.g. 80
  critThreshold?: number // e.g. 90
  height?: number
  showLabel?: boolean
  label?: string
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  warnThreshold = 80,
  critThreshold = 90,
  height = 8,
  showLabel = false,
  label,
}) => {
  const pct = Math.min(Math.max((value / max) * 100, 0), 100)

  let barColor = 'var(--color-safe-green)'
  if (pct >= critThreshold) {
    barColor = 'var(--color-crit-red)'
  } else if (pct >= warnThreshold) {
    barColor = 'var(--color-warn-amber)'
  }

  return (
    <div style={{ width: '100%' }}>
      {showLabel && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '12px',
            marginBottom: '4px',
            color: 'var(--color-ink-300)',
          }}
        >
          <span>{label || 'Utilization'}</span>
          <span style={{ fontWeight: 700, color: barColor }}>{pct.toFixed(1)}%</span>
        </div>
      )}
      <div
        role="progressbar"
        aria-label={label || 'Utilization'}
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        style={{
          width: '100%',
          height: `${height}px`,
          backgroundColor: 'var(--color-ink-750)',
          borderRadius: `${height / 2}px`,
          overflow: 'hidden',
          position: 'relative',
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: '100%',
            backgroundColor: barColor,
            borderRadius: `${height / 2}px`,
            transition: 'width 0.3s ease, background-color 0.3s ease',
          }}
        />
      </div>
    </div>
  )
}
