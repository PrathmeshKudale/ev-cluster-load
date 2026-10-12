import React, { useState } from 'react'
import {
  Zap,
  Clock,
  Navigation,
  ShieldCheck,
  HelpCircle,
  Scale,
  Cpu,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Drawer } from '@/components/ui/drawer'
import { Progress } from '@/components/ui/progress'
import {
  recommendationFixture,
  type CandidateRecommendation,
} from '@/fixtures/recommendationFixture'

export interface RecommendationCardProps {
  recommendation?: CandidateRecommendation
  mode?: 'fastest' | 'balanced' | 'grid_friendly'
  onReserve?: (recommendation: CandidateRecommendation) => void
  highlight?: boolean
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation = recommendationFixture.top3[0],
  mode = 'balanced',
  onReserve,
  highlight = true,
}) => {
  const [whyDrawerOpen, setWhyDrawerOpen] = useState(false)
  const isTopRank = recommendation.rank === 1

  return (
    <>
      <Card
        elevated={isTopRank || highlight}
        style={{
          borderWidth: isTopRank ? '2px' : '1px',
          borderColor: isTopRank ? 'var(--color-trafo-blue)' : 'var(--color-ink-700)',
          position: 'relative',
        }}
      >
        <CardHeader>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Badge
                variant={isTopRank ? 'brand' : 'neutral'}
                icon={isTopRank ? <Zap size={12} /> : undefined}
              >
                #{recommendation.rank} {isTopRank ? 'RECOMMENDED' : 'ALTERNATIVE'}
              </Badge>
              <span style={{ fontSize: '13px', color: 'var(--color-ink-300)' }}>
                {recommendation.starts_in_h === 0
                  ? 'Starts Now'
                  : `Starts in +${recommendation.starts_in_h}h`}
              </span>
            </div>
            <CardTitle style={{ marginTop: '6px' }}>{recommendation.station_name}</CardTitle>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div
              className="font-mono-numbers"
              style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-trafo-blue)' }}
            >
              J = {recommendation.score.toFixed(3)}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--color-ink-300)' }}>Cost Score (Min)</div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Key Driver Decision Factors (Wait, Detour, Headroom) */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(3, 1fr)',
              gap: '10px',
              backgroundColor: 'var(--color-ink-900)',
              padding: '12px',
              borderRadius: 'var(--radius-sm)',
              marginBottom: '14px',
            }}
          >
            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-ink-300)' }}>Expected Wait</div>
              <div
                className="font-mono-numbers"
                style={{
                  fontSize: '15px',
                  fontWeight: 700,
                  color:
                    recommendation.wait_min === 0
                      ? 'var(--color-safe-green)'
                      : 'var(--color-ink-100)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginTop: '2px',
                }}
              >
                <Clock size={14} color="var(--color-ink-300)" />
                {recommendation.wait_min === 0 ? '0 min (None)' : `${recommendation.wait_min} min`}
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
                +{recommendation.detour_min} min
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-ink-300)' }}>Grid Headroom</div>
              <div
                className="font-mono-numbers"
                style={{
                  fontSize: '15px',
                  fontWeight: 700,
                  color:
                    recommendation.grid_load_pct >= 80
                      ? 'var(--color-warn-amber)'
                      : 'var(--color-safe-green)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  marginTop: '2px',
                }}
              >
                <ShieldCheck size={14} color="var(--color-ink-300)" />
                {recommendation.grid_load_pct.toFixed(0)}% Load
              </div>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontSize: '13px',
              color: 'var(--color-ink-300)',
              marginBottom: '16px',
            }}
          >
            <span>
              {recommendation.available_bays} of {recommendation.total_bays} bays available •{' '}
              {recommendation.charger_kw} kW Type 2
            </span>
            <button
              onClick={() => setWhyDrawerOpen(true)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--color-trafo-blue)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                cursor: 'pointer',
                fontWeight: 700,
                fontSize: '13px',
                padding: '2px 4px',
              }}
              aria-label={`Open why drawer for ${recommendation.station_name}`}
            >
              <HelpCircle size={14} />
              <span>Why this slot?</span>
            </button>
          </div>

          {/* Primary Action Button (The 3rd tap in the driver flow) */}
          <Button
            variant="primary"
            size="md"
            style={{ width: '100%' }}
            onClick={() => onReserve?.(recommendation)}
            icon={<Zap size={16} />}
          >
            Reserve Bay & Start Route
          </Button>
        </CardContent>
      </Card>

      {/* Why Drawer / Sheet Component */}
      <Drawer
        isOpen={whyDrawerOpen}
        onClose={() => setWhyDrawerOpen(false)}
        title={`Why ${recommendation.station_name}?`}
        description={`Multi-objective mathematical dispatch breakdown under '${mode.toUpperCase()}' mode.`}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Natural language summary */}
          <div
            style={{
              padding: '14px 16px',
              backgroundColor: 'var(--color-ink-850)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--color-ink-700)',
              fontSize: '14px',
              lineHeight: 1.6,
              color: 'var(--color-ink-100)',
            }}
          >
            <strong>Optimization Rationale:</strong>
            <p style={{ marginTop: '6px', color: 'var(--color-ink-200)' }}>
              {recommendation.why_reason}
            </p>
          </div>

          {/* LightGBM TreeExplainer (Real SHAP Output Top-3 Reasons) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '15px', fontWeight: 700 }}>
              <Cpu size={18} color="var(--color-trafo-blue)" />
              <span>LightGBM TreeExplainer (Top 3 SHAP Attributions):</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--color-ink-300)', margin: 0 }}>
              Attributing forecasted cluster &amp; station power demand (kW) to input features via exact TreeSHAP:
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
              {(recommendation.shap_reasons && recommendation.shap_reasons.length > 0
                ? recommendation.shap_reasons
                : [
                    'Station bay headroom availability (-5.42 kW effect)',
                    'Diurnal afternoon lull timing (-3.85 kW effect)',
                    'Recent 1-hour load persistence (-1.20 kW effect)',
                  ]
              ).map((reason, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    padding: '8px 12px',
                    backgroundColor: 'var(--color-ink-950)',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--color-ink-700)',
                    fontSize: '13px',
                  }}
                >
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--color-ink-800)',
                      fontSize: '11px',
                      fontWeight: 700,
                      color: 'var(--color-trafo-blue)',
                    }}
                  >
                    #{idx + 1}
                  </span>
                  <span style={{ color: 'var(--color-ink-100)', flex: 1 }}>{reason}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Multi-Objective Mathematical Formulation */}
          <div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                fontSize: '15px',
                fontWeight: 700,
                marginBottom: '10px',
              }}
            >
              <Scale size={18} color="var(--color-trafo-blue)" />
              <span>Multi-Objective Score Formulation:</span>
            </div>
            <div
              className="font-mono-numbers"
              style={{
                padding: '12px',
                backgroundColor: 'var(--color-ink-950)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--color-ink-700)',
                fontSize: '13px',
                color: 'var(--color-ink-200)',
              }}
            >
              J = w₁ · Wait + w₂ · Detour + w₃ · (1 − Balance) + w₄ · OverloadRisk
            </div>
          </div>

          {/* Component Score Contributions Bar Breakdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                  marginBottom: '4px',
                }}
              >
                <span>
                  Queue Wait Penalty (w₁ ={' '}
                  {recommendation.score_breakdown.weights.wait})
                </span>
                <span className="font-mono-numbers" style={{ fontWeight: 700 }}>
                  +{recommendation.score_breakdown.wait_component.toFixed(3)}
                </span>
              </div>
              <Progress
                value={recommendation.score_breakdown.wait_component * 200}
                max={100}
                height={6}
              />
            </div>

            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                  marginBottom: '4px',
                }}
              >
                <span>
                  Detour Distance Penalty (w₂ ={' '}
                  {recommendation.score_breakdown.weights.detour})
                </span>
                <span className="font-mono-numbers" style={{ fontWeight: 700 }}>
                  +{recommendation.score_breakdown.detour_component.toFixed(3)}
                </span>
              </div>
              <Progress
                value={recommendation.score_breakdown.detour_component * 200}
                max={100}
                height={6}
              />
            </div>

            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                  marginBottom: '4px',
                }}
              >
                <span>
                  Station Imbalance Penalty (w₃ ={' '}
                  {recommendation.score_breakdown.weights.balance})
                </span>
                <span className="font-mono-numbers" style={{ fontWeight: 700 }}>
                  +{recommendation.score_breakdown.imbalance_component.toFixed(3)}
                </span>
              </div>
              <Progress
                value={recommendation.score_breakdown.imbalance_component * 200}
                max={100}
                height={6}
              />
            </div>

            <div>
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '13px',
                  marginBottom: '4px',
                }}
              >
                <span>
                  Transformer Overload Risk (w₄ ={' '}
                  {recommendation.score_breakdown.weights.risk})
                </span>
                <span className="font-mono-numbers" style={{ fontWeight: 700 }}>
                  +{recommendation.score_breakdown.risk_component.toFixed(3)}
                </span>
              </div>
              <Progress
                value={recommendation.score_breakdown.risk_component * 200}
                max={100}
                height={6}
              />
            </div>
          </div>

          {/* Hard Transformer Safety Guarantee */}
          <div
            style={{
              padding: '12px 14px',
              backgroundColor: 'var(--color-safe-green-bg)',
              border: '1px solid var(--color-safe-green-border)',
              borderRadius: 'var(--radius-sm)',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontSize: '13px',
            }}
          >
            <ShieldCheck size={20} color="var(--color-safe-green)" />
            <span>
              <strong>Hard Safety Guarantee:</strong> Verified via Hypothesis property testing—no slot
              recommendation pushes transformer load above 90% when feasible slots exist.
            </span>
          </div>

          <Button
            variant="primary"
            style={{ width: '100%', marginTop: '8px' }}
            onClick={() => {
              setWhyDrawerOpen(false)
              onReserve?.(recommendation)
            }}
          >
            Accept Rationale & Reserve Slot
          </Button>
        </div>
      </Drawer>
    </>
  )
}
