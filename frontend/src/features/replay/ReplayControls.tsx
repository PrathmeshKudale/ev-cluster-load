import React, { useState } from 'react'
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  FastForward,
  Clock,
  TrendingDown,
  Award,
  ShieldCheck,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Slider } from '@/components/ui/slider'
import { replayFixture, type ReplayStateFixture } from '@/fixtures/replayFixture'

export interface ReplayControlsProps {
  initialState?: ReplayStateFixture
  onPlayChange?: (isPlaying: boolean) => void
  onSpeedChange?: (speed: 1 | 10 | 60) => void
  onSeek?: (stepHours: number) => void
}

export const ReplayControls: React.FC<ReplayControlsProps> = ({
  initialState = replayFixture,
  onPlayChange,
  onSpeedChange,
  onSeek,
}) => {
  const [isPlaying, setIsPlaying] = useState(initialState.is_playing)
  const [speed, setSpeed] = useState<1 | 10 | 60>(initialState.speed_multiplier)
  const [currentStep, setCurrentStep] = useState(initialState.current_step_hours)

  const togglePlay = () => {
    const next = !isPlaying
    setIsPlaying(next)
    onPlayChange?.(next)
  }

  const handleSpeedSelect = (s: 1 | 10 | 60) => {
    setSpeed(s)
    onSpeedChange?.(s)
  }

  const handleSeekChange = (val: number) => {
    setCurrentStep(val)
    onSeek?.(val)
  }

  const stepForward = () => {
    const next = Math.min(currentStep + 1, initialState.total_horizon_hours)
    setCurrentStep(next)
    onSeek?.(next)
  }

  const stepBack = () => {
    const next = Math.max(currentStep - 1, 0)
    setCurrentStep(next)
    onSeek?.(next)
  }

  const resetTimeline = () => {
    setCurrentStep(0)
    onSeek?.(0)
  }

  const dayNumber = Math.floor(currentStep / 24) + 1
  const hourOfDay = currentStep % 24

  return (
    <Card style={{ width: '100%' }}>
      <CardHeader>
        <div>
          <CardTitle style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FastForward size={20} color="var(--color-trafo-blue)" />
            <span>Simulation Replay & Benchmark Controls</span>
          </CardTitle>
          <p style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
            Accelerated Discrete-Event Playback (SimPy FCFS vs. Smart Dispatch)
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <Badge variant="brand" icon={<Clock size={12} />}>
            Day {dayNumber}, {String(hourOfDay).padStart(2, '0')}:00 UTC
          </Badge>
          <Badge variant="normal" icon={<ShieldCheck size={12} />}>
            {isPlaying ? 'PLAYING' : 'PAUSED'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        {/* Timeline Seek Slider */}
        <div style={{ marginBottom: '18px' }}>
          <Slider
            value={currentStep}
            min={0}
            max={initialState.total_horizon_hours}
            step={1}
            onChange={handleSeekChange}
            label={`Simulation Progress: ${currentStep} / ${initialState.total_horizon_hours} hours (${((currentStep / initialState.total_horizon_hours) * 100).toFixed(0)}%)`}
          />
        </div>

        {/* Playback Control Bar */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            backgroundColor: 'var(--color-ink-900)',
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--color-ink-700)',
            marginBottom: '18px',
          }}
        >
          {/* Playback transport buttons */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Button
              variant="outline"
              size="sm"
              onClick={resetTimeline}
              aria-label="Restart timeline"
              title="Restart timeline"
            >
              <RotateCcw size={15} />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={stepBack}
              aria-label="Step back 1 hour"
              title="Step back 1 hour"
            >
              <SkipBack size={15} />
            </Button>
            <Button
              variant={isPlaying ? 'warning' : 'primary'}
              size="md"
              onClick={togglePlay}
              icon={isPlaying ? <Pause size={16} /> : <Play size={16} />}
              style={{ minWidth: '110px' }}
            >
              {isPlaying ? 'PAUSE' : 'PLAY'}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={stepForward}
              aria-label="Step forward 1 hour"
              title="Step forward 1 hour"
            >
              <SkipForward size={15} />
            </Button>
          </div>

          {/* Speed multiplier selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span style={{ fontSize: '13px', color: 'var(--color-ink-300)', marginRight: '4px' }}>
              Speed:
            </span>
            {([1, 10, 60] as const).map((s) => (
              <Button
                key={s}
                variant={speed === s ? 'primary' : 'outline'}
                size="sm"
                onClick={() => handleSpeedSelect(s)}
                style={{ padding: '4px 10px', minHeight: '32px' }}
              >
                {s}x
              </Button>
            ))}
          </div>
        </div>

        {/* Side-by-side Benchmark Metrics Summary */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '12px',
          }}
        >
          <div
            style={{
              padding: '12px',
              backgroundColor: 'var(--color-ink-850)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-ink-700)',
            }}
          >
            <div style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Peak Shaving</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--color-safe-green)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '4px',
              }}
            >
              <TrendingDown size={16} />
              -{initialState.metrics.improvement.peak_shaving_pct}%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
              88.5 kW → 74.2 kW (-14.3 kW)
            </div>
          </div>

          <div
            style={{
              padding: '12px',
              backgroundColor: 'var(--color-ink-850)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-ink-700)',
            }}
          >
            <div style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Queue Wait Cut</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--color-safe-green)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '4px',
              }}
            >
              <TrendingDown size={16} />
              -{initialState.metrics.improvement.wait_reduction_pct}%
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
              18.6m → 8.1m avg delay
            </div>
          </div>

          <div
            style={{
              padding: '12px',
              backgroundColor: 'var(--color-ink-850)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-ink-700)',
            }}
          >
            <div style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Overload &gt;90%</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--color-safe-green)',
                marginTop: '4px',
              }}
            >
              0.0 hrs (0%)
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
              100% Eliminated (FCFS: 1.2h)
            </div>
          </div>

          <div
            style={{
              padding: '12px',
              backgroundColor: 'var(--color-ink-850)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--color-ink-700)',
            }}
          >
            <div style={{ fontSize: '12px', color: 'var(--color-ink-300)' }}>Jain's Fairness</div>
            <div
              className="font-mono-numbers"
              style={{
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--color-trafo-blue)',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                marginTop: '4px',
              }}
            >
              <Award size={16} />
              {initialState.metrics.smart.jain_fairness.toFixed(2)}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)', marginTop: '2px' }}>
              Balanced load (+16.0%)
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
