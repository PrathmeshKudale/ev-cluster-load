import React from 'react'

export interface SliderProps {
  value: number
  min?: number
  max?: number
  step?: number
  onChange: (value: number) => void
  disabled?: boolean
  label?: string
}

export const Slider: React.FC<SliderProps> = ({
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  disabled = false,
  label,
}) => {
  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '6px' }}>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--color-ink-300)' }}>
          <span>{label}</span>
          <span className="font-mono-numbers" style={{ color: 'var(--color-ink-100)', fontWeight: 700 }}>
            {value}
          </span>
        </div>
      )}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{
          width: '100%',
          accentColor: 'var(--color-trafo-blue)',
          cursor: disabled ? 'not-allowed' : 'pointer',
          height: '6px',
        }}
      />
    </div>
  )
}
