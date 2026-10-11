# EV Cluster Load Dispatcher — Component Architecture

> **Document Status**: Production Ready  
> **Target Release**: Frontend v1.0 (`feat/f1-components`)  
> **Design Foundations**: Atkinson Hyperlegible, WCAG AA, Substation Thermal Derating, 80% Warn / 90% Crit Thresholds  
> **Interactive Catalog**: `/components` in the running frontend application

---

## 1. Architecture Overview

The frontend follows a **domain-driven feature architecture** combined with a shared `ui` primitive layer following the **shadcn/ui** pattern (un-opinionated, accessible, composable primitives styled with project CSS variables).

```
frontend/src/
├── components/
│   ├── AppShell.tsx           # Global responsive app frame, persona switcher, nav tabs
│   └── ui/                    # shadcn/ui style accessible primitives
│       ├── alert.tsx          # Callout boxes (info, warn, crit, success)
│       ├── badge.tsx          # Severity pills & metadata tags
│       ├── button.tsx         # High-contrast action buttons
│       ├── card.tsx           # Framed surface containers
│       ├── drawer.tsx         # Accessible slide-up sheet (Why Drawer)
│       ├── progress.tsx       # Threshold-aware loading / utilization bars
│       ├── slider.tsx         # Simulation scrubber & control sliders
│       └── tabs.tsx           # Accessible tab list
├── features/
│   ├── cluster/
│   │   ├── ClusterMap.tsx     # SVG topology diagram & ST-GNN cluster visualizer
│   │   ├── StationCard.tsx    # Individual charging station & bay grid card
│   │   └── index.ts
│   ├── forecast/
│   │   ├── ForecastBandChart.tsx # 24h P10/P50/P90 quantile band & ToD tariff ribbon
│   │   └── index.ts
│   ├── recommend/
│   │   ├── RecommendationCard.tsx # Ranked slot card + interactive Why Drawer
│   │   └── index.ts
│   ├── replay/
│   │   ├── ReplayControls.tsx # 168h simulation transport & comparative benchmarks
│   │   └── index.ts
│   └── transformer/
│       ├── TransformerGauge.tsx # 180° radial arc gauge & thermal derating stats
│       ├── AlertFeed.tsx        # Substation threshold stream & action triggers
│       └── index.ts
├── fixtures/                  # Standalone mock payloads for offline rendering
│   ├── alertFixture.ts
│   ├── clusterFixture.ts
│   ├── forecastFixture.ts
│   ├── recommendationFixture.ts
│   ├── replayFixture.ts
│   ├── stationsFixture.ts
│   └── transformerFixture.ts
└── pages/
    └── ComponentsPage.tsx     # Live interactive catalog mounting every component
```

---

## 2. Design Tokens & Visual Hierarchy

All components are styled using CSS custom properties declared in `src/index.css`:

| Token | CSS Variable | Value | Purpose |
| :--- | :--- | :--- | :--- |
| **Ink 950** | `--color-ink-950` | `#051317` | Canvas background |
| **Ink 900** | `--color-ink-900` | `#0a1f24` | Surface cards & panels (Deep Teal Ink) |
| **Ink 700** | `--color-ink-700` | `#183e47` | Subtle border dividers |
| **Transformer Blue** | `--color-trafo-blue`| `#1e88e5` | Primary brand accent & active states |
| **Warning Amber** | `--color-warn-amber` | `#d97706` | **80% Substation Warning Threshold** |
| **Critical Red** | `--color-crit-red` | `#dc2626` | **90% Substation Critical Limit** |
| **Safe Green** | `--color-safe-green` | `#059669` | Below 80% normal operating limit |
| **Sans Typography** | `--font-sans` | `Atkinson Hyperlegible` | Legibility for low-vision & fast scans |
| **Mono Typography** | `--font-mono` | `JetBrains Mono` | Tabular metrics, kW, kVA, timestamps |

---

## 3. Core Feature Components

### 3.1. `ClusterMap`
- **Location**: `src/features/cluster/ClusterMap.tsx`
- **Props**:
  ```typescript
  export interface ClusterMapProps {
    data?: ClusterFixture;
    onSelectStation?: (stationId: string) => void;
  }
  ```
- **Description**: An interactive SVG topology map representing the ST-GNN spatial cluster. Displays the 100 kVA substation transformer (T1) at the top, feeder radial lines branching to 4 charging stations (S1 Market Road, S2 Station Plaza, S3 College Gate, S4 Ring Road Hub), and bidirectional inter-station routing lines with Haversine/OSRM travel times.
- **Fixture Binding**: Defaults to `clusterFixture` (`src/fixtures/clusterFixture.ts`).
- **Key Interactions**:
  - Clicking any station node highlights it and triggers `onSelectStation(id)`.
  - Hovering reveals drive time in minutes and distance in km.
  - Color-coded badges for station status (Available, Busy, Full).

---

### 3.2. `StationCard`
- **Location**: `src/features/cluster/StationCard.tsx`
- **Props**:
  ```typescript
  export interface StationCardProps {
    station?: StationDetailFixture;
    onSelect?: (stationId: string) => void;
    selected?: boolean;
  }
  ```
- **Description**: Compact card representing a charging hub. Displays available plugs, total plugs, Erlang-C wait time, detour overhead, active power in kW, and a visual grid of individual bay plugs with status pills (Available, Occupied, Reserved).
- **Fixture Binding**: Defaults to `stationsFixture[0]` (`src/fixtures/stationsFixture.ts`).
- **Severity Dynamics**:
  - Normal (`<80%`): Safe green border.
  - High Queue (`>=80%`): Amber warning border.
  - All Full (`0` available): Red critical border with alert banner.

---

### 3.3. `ForecastBandChart`
- **Location**: `src/features/forecast/ForecastBandChart.tsx`
- **Props**:
  ```typescript
  export interface ForecastBandChartProps {
    data?: ForecastFixture;
    onHoverHour?: (hour: number) => void;
  }
  ```
- **Description**: 24-hour calibrated quantile load forecast chart. Renders the conformal quantile prediction band from LightGBM:
  - **P10 (Lower bound)**: Dotted teal line.
  - **P50 (Median expected)**: Solid Transformer Blue line.
  - **P90 (Worst-case load)**: Dashed red/amber line with filled semi-transparent uncertainty band.
  - **80% Warning Limit**: Dashed amber horizontal line.
  - **90% Critical Limit**: Dashed red horizontal line.
  - **ToD Tariff Ribbon**: Color-coded bar along the bottom indicating Off-Peak (₹5.50/kWh), Normal (₹7.50/kWh), and Peak (₹10.50/kWh) intervals.
- **Fixture Binding**: Defaults to `forecastFixture` (`src/fixtures/forecastFixture.ts`).
- **Key Interactions**:
  - Interactive mouse hover across the 24 hours displays exact kW, kVA, and P10/P50/P90 numbers in a real-time tooltip pill.

---

### 3.4. `TransformerGauge`
- **Location**: `src/features/transformer/TransformerGauge.tsx`
- **Props**:
  ```typescript
  export interface TransformerGaugeProps {
    data?: TransformerFixture;
  }
  ```
- **Description**: Semi-circular (180°) radial arc gauge displaying real-time transformer loading percentage against rated kVA.
  - Visible ticks and color thresholds at 80% (Warning) and 90% (Critical).
  - Animated needle indicating current load (78.1 kVA / 78.1%).
  - Ambient temperature derating factor display (32.5°C -> 0.982 derate factor -> 98.2 kVA effective capacity).
  - Pandapower load flow stats (Feeder voltage drop: 3.49%, safe under 5.0% grid code).
- **Fixture Binding**: Defaults to `transformerFixture` (`src/fixtures/transformerFixture.ts`).

---

### 3.5. `RecommendationCard` (with Why Drawer)
- **Location**: `src/features/recommend/RecommendationCard.tsx`
- **Props**:
  ```typescript
  export interface RecommendationCardProps {
    recommendation?: CandidateRecommendation;
    mode?: 'fastest' | 'balanced' | 'grid_friendly';
    onReserve?: (recommendation: CandidateRecommendation) => void;
    highlight?: boolean;
  }
  ```
- **Description**: Candidate dispatch card for drivers and operators.
  - Shows slot rank (`#1 RECOMMENDED`, `#2 ALTERNATIVE`), station name, queue wait time, detour overhead, and expected transformer load impact.
  - **"Why This Slot?" Button**: Opens an accessible slide-up sheet (`Drawer`) that explains the mathematical multi-objective scoring formula:
    $$J = w_1 \cdot \text{wait} + w_2 \cdot \text{detour} + w_3 \cdot (1 - \text{balance}) + w_4 \cdot \text{risk}$$
    Displays the AHP pairwise weights ($w_1, w_2, w_3, w_4$), the Erlang-C wait calculation, utilization balance, and the P90 cluster overload headroom.
  - **One-Tap "Reserve Slot" Button**: Completes the 3-tap driver recommendation flow.
- **Fixture Binding**: Defaults to `recommendationFixture.top3[0]` (`src/fixtures/recommendationFixture.ts`).

---

### 3.6. `ReplayControls`
- **Location**: `src/features/replay/ReplayControls.tsx`
- **Props**:
  ```typescript
  export interface ReplayControlsProps {
    initialState?: ReplayStateFixture;
    onPlayChange?: (isPlaying: boolean) => void;
    onSpeedChange?: (speed: 1 | 10 | 60) => void;
    onSeek?: (stepHours: number) => void;
  }
  ```
- **Description**: Interactive simulation timeline transport controls for operators and analysts.
  - **Transport Buttons**: Play, Pause, Step Back (-1h), Step Forward (+1h), Reset.
  - **Speed Multipliers**: `1x` (Real-time), `10x` (Fast), `60x` (1 min = 1 hour).
  - **Timeline Scrubber**: Slider scrubbable from hour 0 to 168 (7-day horizon).
  - **Comparative Benchmarks**: Displays live comparative telemetry between **FCFS (Baseline)** vs **Smart Dispatch (GridFlow)**:
    - Peak Transformer Load: 94.2% vs 84.1% (-10.1% peak shaving)
    - Mean Driver Wait Time: 14.8 min vs 6.2 min (-58.1% wait reduction)
    - Total Overload Violations: 12 events vs 0 events (-100% overload elimination)
- **Fixture Binding**: Defaults to `replayFixture` (`src/fixtures/replayFixture.ts`).

---

### 3.7. `AlertFeed`
- **Location**: `src/features/transformer/AlertFeed.tsx`
- **Props**:
  ```typescript
  export interface AlertFeedProps {
    alerts?: AlertItem[];
    onAcknowledge?: (alertId: string) => void;
    onAction?: (alert: AlertItem) => void;
    maxItems?: number;
  }
  ```
- **Description**: Real-time event stream of substation threshold crossings, high-queue alerts, and tariff transitions.
  - Distinct severity left-borders (Critical Red, Warning Amber, Info Blue).
  - Entity pills (TRANSFORMER T1, STATION S4, GRID ToD).
  - Filter tabs (`All`, `Active`, `Critical`).
  - Contextual action buttons (`Reroute Drivers`, `Review Headroom`, `Dismiss`).
  - Screen reader announcements via `role="article"` and `aria-label`.
- **Fixture Binding**: Defaults to `alertFixture` (`src/fixtures/alertFixture.ts`).

---

## 4. Shared UI Primitives (`src/components/ui/`)

| Primitive | File | Features |
| :--- | :--- | :--- |
| `Button` | `button.tsx` | Variants: `primary`, `secondary`, `outline`, `ghost`, `danger`, `warning`. Sizes: `sm`, `md`, `lg`. |
| `Card` | `card.tsx` | Elevated shadows, severity left-borders (`warn`, `crit`, `normal`), header & content subcomponents. |
| `Badge` | `badge.tsx` | Variants: `normal` (green), `warn` (amber), `crit` (red), `brand` (teal), `neutral`. Icon slot. |
| `Drawer` | `drawer.tsx` | Accessible slide-up modal with backdrop blur, Escape key listener, drag handle, and scroll lock. |
| `Progress`| `progress.tsx` | Threshold-aware fill color: green `<80%`, amber `80-90%`, red `>90%`. |
| `Slider` | `slider.tsx` | Accessible range input with custom teal thumb and track styling. |
| `Alert` | `alert.tsx` | Accessible callout with icon, title, description, and action button. |
| `Tabs` | `tabs.tsx` | ARIA-compliant tab list with active indicator pill. |

---

## 5. Live Interactive Catalog: `/components`

Visiting `/components` (or selecting the **Catalog** tab in the navigation bar) mounts `src/pages/ComponentsPage.tsx`.

The catalog features:
1. **Jump to TOC**: Instant anchors to each of the 7 feature components and shared UI primitives.
2. **Autonomous Fixture Rendering**: Every component mounts immediately with realistic domain data without requiring backend connectivity.
3. **Interactive Testing Controls**:
   - Station selector syncing `ClusterMap` and `StationCard`.
   - Live hover readout on `ForecastBandChart`.
   - Live "Why Drawer" expansion on `RecommendationCard`.
   - Functional scrub slider and playback buttons on `ReplayControls`.
   - Live dismiss / filter toggles on `AlertFeed`.

---

## 6. Verification & Build Acceptance

- **TypeScript Compilation**: `tsc -b` passes with zero errors.
- **Vite Production Bundler**: `vite build` bundles `frontend/dist/` in under 300ms.
- **Accessibility Check**: Atkinson Hyperlegible typography loaded, high contrast ratios (`>4.5:1`), explicit focus rings (`:focus-visible`), and ARIA landmarks verified across all components.
