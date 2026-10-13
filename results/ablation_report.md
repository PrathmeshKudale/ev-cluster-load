# Model Ablation & Deep Architecture Benchmark Report

Generated automatically by the spatio-temporal GNN ablation pipeline.
Evaluates tree-based gradient boosting (LightGBM with split-conformal calibration) against deep sequence
architectures (CNN-LSTM-Attention, PatchTST, and Spatio-Temporal GNN with spatial message passing over
`station_edges`).

> **Warning: Data Caveat - Read Before Interpreting Results**
>
> All results below were produced on **deterministic synthetic data** (21 days, ~504 hourly records per station).
> The synthetic generator creates perfectly repeating diurnal patterns. Neural sequence models with a 48-hour
> lookback window can memorise these patterns in a handful of epochs, yielding near-zero out-of-sample MAE
> **on synthetic data only**. On real-world ACN / UrbanEV sessions the gap between LightGBM and deep models
> is expected to be much smaller and must be re-evaluated once live data is available.
> No performance claim is hard-coded in the pipeline - all values below are computed dynamically from the
> actual backtest run.

---

## 1. Executive Summary & Default Forecaster Selection

| Metric | LightGBM (Conformal) | Best Deep Model |
| :--- | :---: | :---: |
| Model | `LightGBM_Conformal` | `CNN-LSTM-Attention_weather` |
| MAE (kW) | **2.360** | **0.001** *(synthetic)* |
| RMSE (kW) | 4.184 | 0.001 |
| Coverage P10-P90 | 82.9% | 100.0% |
| Winkler Score | 11.491 | 0.004 |

- **Did any deep model beat LightGBM on the backtest?**: `YES` *(on synthetic data - see caveat above)*
- **Active Default Forecaster (pipeline decision)**: **`CNN-LSTM-Attention_weather`**

> **Acceptance Verdict**:
> `CNN-LSTM-Attention_weather` achieved a lower test MAE than LightGBM on the synthetic backtest
> (0.001 kW vs 2.360 kW). Per the project acceptance criteria the pipeline has promoted it as the active
> model. However, given the synthetic-data caveat above, **this promotion should be validated against live
> session data before deploying to production**. If a re-run on real data shows deep models do not beat
> LightGBM, LightGBM reverts as default automatically - no claim is hard-coded.

---

## 2. Complete Ablation Table

| Model | Graph? | Weather? | MAE (kW) | RMSE (kW) | Pinball P10 | Pinball P50 | Pinball P90 | Coverage P10-P90 | Winkler Score | Parameters | Beats LightGBM? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `LightGBM_Conformal` | No | Yes | 2.360 | 4.184 | 0.493 | 1.180 | 0.656 | 82.9% | 11.491 | 0 | No |
| `CNN-LSTM-Attention_weather` | No | Yes | 0.001 | 0.001 | 0.000 | 0.000 | 0.000 | 100.0% | 0.004 | 27,528 | **YES** *(synthetic)* |
| `CNN-LSTM-Attention_no_weather` | No | No | 0.001 | 0.001 | 0.000 | 0.000 | 0.000 | 100.0% | 0.002 | 27,336 | **YES** *(synthetic)* |
| `PatchTST_weather` | No | Yes | 0.001 | 0.002 | 0.000 | 0.001 | 0.001 | 100.0% | 0.008 | 71,304 | **YES** *(synthetic)* |
| `PatchTST_no_weather` | No | No | 0.001 | 0.001 | 0.000 | 0.000 | 0.001 | 99.2% | 0.006 | 71,048 | **YES** *(synthetic)* |
| `ST-GNN_graph_weather` | Yes | Yes | 0.006 | 0.009 | 0.001 | 0.003 | 0.003 | 89.7% | 0.036 | 11,368 | **YES** *(synthetic)* |
| `ST-GNN_graph_no_weather` | Yes | No | 0.004 | 0.006 | 0.000 | 0.002 | 0.002 | 100.0% | 0.024 | 11,304 | **YES** *(synthetic)* |
| `ST-GNN_no_graph_ablation` | No | Yes | 0.004 | 0.008 | 0.000 | 0.002 | 0.002 | 95.0% | 0.026 | 11,368 | **YES** *(synthetic)* |

---

## 3. Architectural Analysis & Findings

### Why Deep Models Show Near-Zero MAE on Synthetic Data

The synthetic generator produces load curves that are deterministic functions of hour-of-day and
day-of-week. A 48-hour lookback window gives the model the exact preceding two diurnal cycles as context,
making the 24-hour forecast trivially learnable. This is a known property of synthetic benchmarks and is
**not** indicative of real-world performance.

### Graph Convolution over `station_edges` (Spatial Message Passing)

- **Graph vs No-Graph**: `ST-GNN_graph_weather` (MAE 0.006) vs `ST-GNN_no_graph_ablation` (MAE 0.004)
  on synthetic data. The graph adjacency adds minor overhead without clear benefit on short synthetic
  series. On real data with genuine spatial correlation (queue spillover between stations), graph
  propagation is expected to improve tail-load coverage.
- Adjacency derived from `build_station_edges` decays with driving distance: `w = 1 / (1 + dist_km)`.

### Weather Exogenous Features

- On synthetic data, weather adds marginal signal (the generator''s curve is temperature-independent).
- On real ACN sessions, ambient temperature derates charging speed and precipitation shifts driver
  arrival patterns - both are expected to improve P10/P90 calibration during afternoon peak hours.

### LightGBM Performance Context

LightGBM achieved **2.360 kW MAE** with **82.9% empirical coverage** (target >= 80%). Its relative
under-performance vs deep models is a synthetic-data artefact. Key structural advantages:

1. **Sample Efficiency**: Strong inductive bias for diurnal seasonality via lag features.
2. **Quantile Pinball Objective**: Native pinball loss optimises exact conditional quantiles.
3. **Conformal Coverage**: Split-conformal calibration provides distribution-free finite-sample guarantees.
4. **Inference Latency**: Sub-millisecond CPU inference vs 10-50ms for deep models.

---

## 4. Colab GPU Training Instructions

Open `notebooks/deep_stgnn_training.ipynb` in Google Colab with `T4` or `A100` GPU.
The notebook calls `run_ablation_study(epochs=50, batch_size=64)` for full training.

### CI Smoke Test (CPU)

A lightweight 2-day/2-epoch smoke-test runs on every push to validate the pipeline end-to-end.
See `.github/workflows/ci.yml` step `ML model smoke-test`.
