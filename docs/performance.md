# Performance Baseline

> **Measurement method**: Lighthouse CI v13 in GitHub Actions, 3 runs averaged, desktop preset, production build served by `vite preview`.
> Recorded on: branch `feat/f8-performance` — scores will update after CI runs on the merged build.

## Lighthouse Scores (production build)

| Screen | Performance | Accessibility | Best Practices | SEO |
|:---|:---:|:---:|:---:|:---:|
| `/driver` | ≥ 90 (budget) | ≥ 90 | ≥ 85 | ≥ 80 |
| `/operator` | ≥ 90 (budget) | ≥ 90 | ≥ 85 | ≥ 80 |

> [!NOTE]
> CI will fill in real scores after the first successful pipeline run. The table above shows the minimum budgets enforced by `lighthouserc.json`.

## Bundle Size Budget

| Chunk | Budget | Strategy |
|:---|:---:|:---|
| JS (scripts total) | ≤ 512 KB | Manual chunks: echarts / leaflet / react / query split |
| CSS | ≤ 50 KB | Tailwind v4 purged at build time |
| Total transfer | ≤ 1 MB | Lazy routes, lazy chart/map imports |

## Optimisations Applied

### Route-level code splitting
Every page is `React.lazy()` wrapped in `router.tsx`. Vite splits each route into its own chunk automatically. ECharts and Leaflet are in separate vendor chunks.

### Lazy ECharts
`useECharts.ts` dynamically imports only the ECharts modules used (LineChart, GaugeChart, CanvasRenderer, 4 components). This avoids loading the 800 KB full ECharts bundle on initial page load.

### Lazy Leaflet
`StationMap.tsx` imports `leaflet` and `leaflet.markercluster` inside `useEffect`. Map tiles only load when the map component mounts.

### Marker clustering
`leaflet.markercluster` groups nearby station markers at low zoom levels, avoiding DOM overload for clusters with many stations.

### Time-series downsampling
`useDownsample.ts` implements LTTB (Largest-Triangle-Three-Buckets) algorithm, capping all time-series at **500 data points** regardless of backend response size. Applied in `ForecastBandChart`.

### Memoised charts
`ForecastBandChart`, `TransformerGauge`, `AlertRow`, and `VirtualAlertFeed` are all `React.memo()`'d. `useECharts` skips `setOption` calls when the option hash has not changed.

### WebSocket render throttling
`useThrottledWS.ts` limits re-renders from WS messages to **one per second** using a trailing-edge timer. Incoming data accumulates in a ref; only the latest value flushes to React state.

### Virtualised alert feed
`VirtualAlertFeed.tsx` uses CSS absolute positioning to render only the visible window + `OVERSCAN=5` rows. Regular DOM render is used when the list is ≤ 50 items (threshold avoids virtualisation overhead for short lists).

## Web Vitals Targets

| Metric | Target | Description |
|:---|:---:|:---|
| FCP | < 2.0 s | First Contentful Paint |
| LCP | < 3.5 s | Largest Contentful Paint |
| TBT | < 300 ms | Total Blocking Time |
| CLS | < 0.1 | Cumulative Layout Shift |
| TTI | < 4.0 s | Time to Interactive |
