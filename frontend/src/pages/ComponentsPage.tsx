import React, { useState } from 'react'
import {
  FileCode,
  Sparkles,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Slider } from '@/components/ui/slider'
import { Alert } from '@/components/ui/alert'
import { Tabs } from '@/components/ui/tabs'

// Feature Components
import { ClusterMap, StationCard } from '@/features/cluster'
import { ForecastBandChart } from '@/features/forecast'
import { TransformerGauge, AlertFeed } from '@/features/transformer'
import { RecommendationCard } from '@/features/recommend'
import { ReplayControls } from '@/features/replay'

// Fixtures
import { clusterFixture } from '@/fixtures/clusterFixture'
import { stationsFixture } from '@/fixtures/stationsFixture'
import { forecastFixture } from '@/fixtures/forecastFixture'
import { transformerFixture } from '@/fixtures/transformerFixture'
import { recommendationFixture } from '@/fixtures/recommendationFixture'
import { replayFixture } from '@/fixtures/replayFixture'
import { alertFixture } from '@/fixtures/alertFixture'

export const ComponentsPage: React.FC = () => {
  const [selectedStationId, setSelectedStationId] = useState<string>('S1')
  const [selectedHour, setSelectedHour] = useState<number | null>(null)
  const [demoSliderVal, setDemoSliderVal] = useState<number>(45)

  const selectedStation =
    stationsFixture.find((s) => s.id === selectedStationId) || stationsFixture[0]

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
      {/* Page Header */}
      <section
        style={{
          borderBottom: '1px solid var(--color-ink-700)',
          paddingBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <Badge variant="brand" icon={<Sparkles size={12} />}>
            Design System & Component Library
          </Badge>
          <Badge variant="normal" icon={<FileCode size={12} />}>
            7 Feature Components + 8 UI Primitives
          </Badge>
        </div>
        <h1
          style={{
            fontSize: '32px',
            fontWeight: 700,
            letterSpacing: '-0.02em',
            margin: '0 0 12px 0',
          }}
        >
          GridFlow EV Component Catalog
        </h1>
        <p
          style={{
            fontSize: '15px',
            color: 'var(--color-ink-300)',
            maxWidth: '820px',
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          All components are typed in TypeScript, styled with custom CSS variables honoring
          the Atkinson Hyperlegible typography and color tokens (Deep Teal Ink, Transformer Blue,
          Amber 80% and Red 90% thresholds), and render autonomously from fixture data first.
        </p>

        {/* Quick jump navigation */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            flexWrap: 'wrap',
            marginTop: '20px',
          }}
        >
          <span style={{ fontSize: '12px', color: 'var(--color-ink-400)', fontWeight: 600 }}>
            JUMP TO:
          </span>
          <a href="#cluster-map" className="toc-tag">#ClusterMap</a>
          <a href="#station-card" className="toc-tag">#StationCard</a>
          <a href="#forecast-chart" className="toc-tag">#ForecastBandChart</a>
          <a href="#transformer-gauge" className="toc-tag">#TransformerGauge</a>
          <a href="#recommendation-card" className="toc-tag">#RecommendationCard</a>
          <a href="#replay-controls" className="toc-tag">#ReplayControls</a>
          <a href="#alert-feed" className="toc-tag">#AlertFeed</a>
          <a href="#ui-primitives" className="toc-tag">#UI-Primitives</a>
        </div>
      </section>

      {/* 1. ClusterMap */}
      <section id="cluster-map" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">01</span>
            <div>
              <h2 className="component-title">ClusterMap</h2>
              <p className="component-sub">
                <code>@/features/cluster/ClusterMap.tsx</code> • SVG topology visualization for
                spatial ST-GNN clusters, substation feed lines, and station occupancy.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: ClusterMapProps</Badge>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          <ClusterMap
            data={clusterFixture}
            onSelectStation={(id) => setSelectedStationId(id)}
          />
        </div>
      </section>

      {/* 2. StationCard */}
      <section id="station-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">02</span>
            <div>
              <h2 className="component-title">StationCard</h2>
              <p className="component-sub">
                <code>@/features/cluster/StationCard.tsx</code> • Hub card displaying plug count,
                Type-2 AC power, Erlang-C waiting time, detour overhead, and individual bay statuses.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: StationCardProps</Badge>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '16px',
          }}
        >
          {stationsFixture.map((st) => (
            <StationCard
              key={st.id}
              station={st}
              selected={st.id === selectedStationId}
              onSelect={(id) => setSelectedStationId(id)}
            />
          ))}
        </div>
      </section>

      {/* 3. ForecastBandChart */}
      <section id="forecast-chart" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">03</span>
            <div>
              <h2 className="component-title">ForecastBandChart</h2>
              <p className="component-sub">
                <code>@/features/forecast/ForecastBandChart.tsx</code> • 24-hour calibrated quantile
                forecast chart with P10/P50/P90 bands, 80% warn &amp; 90% crit limits, and ToD tariff ribbon.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: ForecastBandChartProps</Badge>
        </div>

        <div>
          <ForecastBandChart
            data={forecastFixture}
            onHoverHour={(h) => setSelectedHour(h)}
          />
        </div>
      </section>

      {/* 4. TransformerGauge */}
      <section id="transformer-gauge" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">04</span>
            <div>
              <h2 className="component-title">TransformerGauge</h2>
              <p className="component-sub">
                <code>@/features/transformer/TransformerGauge.tsx</code> • Radial 180° gauge with 80% &amp;
                90% thresholds, needle, ambient temperature derating (0.982), and Pandapower load flow stats.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: TransformerGaugeProps</Badge>
        </div>

        <div style={{ maxWidth: '640px' }}>
          <TransformerGauge data={transformerFixture} />
        </div>
      </section>

      {/* 5. RecommendationCard (with Why Drawer) */}
      <section id="recommendation-card" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">05</span>
            <div>
              <h2 className="component-title">RecommendationCard (with Why Drawer)</h2>
              <p className="component-sub">
                <code>@/features/recommend/RecommendationCard.tsx</code> • Dispatch candidate card
                with one-tap reserve and an interactive slide-up "Why Drawer" detailing the mathematical
                objective function J = w1·wait + w2·detour + w3·(1−balance) + w4·risk.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: RecommendationCardProps</Badge>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))',
            gap: '20px',
          }}
        >
          {recommendationFixture.top3.map((rec) => (
            <RecommendationCard
              key={rec.rank}
              recommendation={rec}
              mode="balanced"
              onReserve={(r) => alert(`One-Tap Reserved Bay at ${r.station_name}!`)}
            />
          ))}
        </div>
      </section>

      {/* 6. ReplayControls */}
      <section id="replay-controls" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">06</span>
            <div>
              <h2 className="component-title">ReplayControls</h2>
              <p className="component-sub">
                <code>@/features/replay/ReplayControls.tsx</code> • Simulation transport bar with
                Play/Pause, 1x/10x/60x speeds, 168-hour timeline scrubber slider, and FCFS vs. Smart Dispatch benchmarks.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: ReplayControlsProps</Badge>
        </div>

        <div>
          <ReplayControls
            initialState={replayFixture}
            onPlayChange={(playing) => console.log('Replay playing:', playing)}
            onSeek={(step) => console.log('Seeked to hour:', step)}
          />
        </div>
      </section>

      {/* 7. AlertFeed */}
      <section id="alert-feed" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">07</span>
            <div>
              <h2 className="component-title">AlertFeed</h2>
              <p className="component-sub">
                <code>@/features/transformer/AlertFeed.tsx</code> • Live stream of substation threshold
                violations and station queues with severity borders, quick filters, and acknowledge dismissal.
              </p>
            </div>
          </div>
          <Badge variant="brand">Props: AlertFeedProps</Badge>
        </div>

        <div>
          <AlertFeed
            alerts={alertFixture}
            onAcknowledge={(id) => console.log('Acknowledged alert:', id)}
            onAction={(alt) => alert(`Action triggered for ${alt.id}: ${alt.action_label}`)}
          />
        </div>
      </section>

      {/* 8. Shared UI Primitives */}
      <section id="ui-primitives" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="component-meta-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="component-number">08</span>
            <div>
              <h2 className="component-title">Shared UI Primitives (shadcn/ui Pattern)</h2>
              <p className="component-sub">
                <code>@/components/ui/</code> • Core accessible UI building blocks styled with design tokens.
              </p>
            </div>
          </div>
          <Badge variant="brand">shadcn/ui style</Badge>
        </div>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '20px',
          }}
        >
          {/* Button Variants */}
          <Card>
            <CardHeader>
              <CardTitle>Button Variants</CardTitle>
            </CardHeader>
            <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <Button variant="primary">Primary</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
              </div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <Button variant="warning">Warning (80%)</Button>
                <Button variant="danger">Danger (90%)</Button>
                <Button size="sm">Small</Button>
                <Button size="lg">Large</Button>
              </div>
            </CardContent>
          </Card>

          {/* Badge Variants */}
          <Card>
            <CardHeader>
              <CardTitle>Badge Severity</CardTitle>
            </CardHeader>
            <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                <Badge variant="normal">Normal (&lt;80%)</Badge>
                <Badge variant="warn">Warning (80-90%)</Badge>
                <Badge variant="crit">Critical (&gt;90%)</Badge>
                <Badge variant="brand">Brand Teal</Badge>
                <Badge variant="neutral">Neutral Ink</Badge>
              </div>
            </CardContent>
          </Card>

          {/* Progress Thresholds */}
          <Card>
            <CardHeader>
              <CardTitle>Progress (Threshold-Aware)</CardTitle>
            </CardHeader>
            <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span>Safe Load</span>
                  <span style={{ color: 'var(--color-safe-green)' }}>55%</span>
                </div>
                <Progress value={55} />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span>Warning Threshold</span>
                  <span style={{ color: 'var(--color-warn-amber)' }}>84%</span>
                </div>
                <Progress value={84} />
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
                  <span>Critical Overload</span>
                  <span style={{ color: 'var(--color-crit-red)' }}>94%</span>
                </div>
                <Progress value={94} />
              </div>
            </CardContent>
          </Card>

          {/* Slider & Alert */}
          <Card>
            <CardHeader>
              <CardTitle>Slider &amp; Alert Box</CardTitle>
            </CardHeader>
            <CardContent style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
                  <span>Interactive Slider</span>
                  <span style={{ fontFamily: 'var(--font-mono)' }}>{demoSliderVal} %</span>
                </div>
                <Slider
                  value={demoSliderVal}
                  onChange={(v) => setDemoSliderVal(v)}
                  min={0}
                  max={100}
                />
              </div>

              <div>
                <div style={{ fontSize: '12px', marginBottom: '8px' }}>
                  <span>Accessible Tabs</span>
                </div>
                <Tabs
                  activeId="tab1"
                  onChange={() => {}}
                  items={[
                    { id: 'tab1', label: 'Feeder TX' },
                    { id: 'tab2', label: 'Erlang-C' },
                    { id: 'tab3', label: 'Quantiles' },
                  ]}
                />
              </div>

              <Alert variant="warn" title="Feeder Overload Guard">
                Recommendation engine activates soft-queue when P90 transformer load reaches 85%.
              </Alert>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}
