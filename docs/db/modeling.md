# Data Modeling Architecture

This document explains the data pipeline layers, graph modeling, externalized configuration tables, and deterministic seeding mechanism in EV Cluster Load.

## 1. Architectural Layers

The database is divided into three distinct schemas representing stages of data refinement:

### `raw` Schema (Immutable Ingestion)
- **Purpose**: Stores ingested data exactly as received from external APIs (ACN-Data, UrbanEV, Open-Meteo) and hardware protocols (OCPP 1.6J `MeterValues`).
- **Characteristics**:
  - Write-only append log.
  - Retains original JSON payloads and raw string timestamps for forensic auditing.
  - Zero transformations or deduplication.
- **Key Tables**: `raw.acn_sessions`, `raw.weather_observations`, `raw.station_telemetry`.

### `clean` Schema (Typed, Deduplicated, UTC)
- **Purpose**: Canonical relational and analytical data model representing the EV charging cluster.
- **Characteristics**:
  - Strongly typed columns with referential integrity foreign keys.
  - All timestamps converted and stored as UTC `timestamptz`.
  - Privacy guarantee: User identifiers are strictly one-way hashed with SHA-256 (`user_hash`); no personal identifiable information (PII) is stored.
  - Partitioned via TimescaleDB hypertables for time-series scalability (`clean.sessions`, `clean.station_load`, `clean.weather`, `clean.forecasts`).
- **Key Tables**: `clean.clusters`, `clean.transformers`, `clean.stations`, `clean.chargers`, `clean.sessions`, `clean.station_load`, `clean.weather`, `clean.forecasts`, `clean.transformer_risk`, `clean.recommendations`.

### `features` Schema (Model-Ready Representations & Graph)
- **Purpose**: Feature matrices and graph topology optimized for machine learning (LightGBM quantile forecaster and Spatio-Temporal Graph Neural Network).
- **Characteristics**:
  - Hourly tabular lag features, rolling statistics, calendar indicators, ambient temperature, and tariff multipliers.
  - Spatial adjacency matrices connecting charging stations within the cluster.
- **Key Tables**: `features.station_edges`, `features.hourly_cluster_features`.

---

## 2. Spatio-Temporal GNN Graph (`station_edges`)

To forecast the whole charging cluster as a topological graph rather than isolated stations, we represent the charging cluster as a directed graph $G = (V, E, W)$:
- **Nodes $V$**: The 4 charging stations in the cluster (`S1`, `S2`, `S3`, `S4`).
- **Edges $E$**: Directed pairs $(s_i, s_j)$ for $i \ne j$.
- **Attributes**:
  - `distance_km`: Road driving distance from OSRM (`/route/v1/driving`) or spherical Haversine fallback.
  - `drive_minutes`: Driving duration in minutes (computed via OSRM speed profiles or estimated at 28 km/h urban velocity).
  - `weight`: Spatial decay adjacency weight $W_{ij} = \frac{1}{1 + \text{distance\_km}}$, used in GNN message passing layers to share spatial demand correlations.

---

## 3. Externalized Configuration Tables

Hardcoded engineering constants have been moved entirely out of application code into relational configuration tables:

1. **`clean.config_transformer`**:
   - Substation transformer nameplate capacity (`nominal_kva = 100.0`).
   - Power factor (`0.95`).
   - Warning threshold (`0.80`, or 80% kVA) and Critical threshold (`0.90`, or 90% kVA).
   - Cooling class (`ONAN`) and reference ambient temperature (`30.0°C`).

2. **`clean.config_derating_curve`**:
   - Represents IEEE/IEC thermal derating of distribution transformers under high ambient temperatures:
     - 25°C: 1.05 (Cold margin)
     - 30°C: 1.00 (Nominal baseline)
     - 35°C: 0.96 (Mild derating)
     - 40°C: 0.91 (Hot summer derating)
     - 45°C: 0.85 (Severe summer peak)
     - 50°C: 0.77 (Emergency heatwave ceiling)

3. **`clean.config_tod_tariff`**:
   - Indian DISCOM Time-of-Day (ToD) tariff structure to incentivize off-peak charging:
     - Night Off-Peak (23:00–06:00): ₹5.00/kWh (0.85× base multiplier)
     - Morning Normal (06:00–09:00): ₹6.50/kWh (1.00× base multiplier)
     - Solar Off-Peak (09:00–17:00): ₹5.50/kWh (0.85× base multiplier)
     - Evening Peak (17:00–23:00): ₹8.50/kWh (1.25× base multiplier)

---

## 4. Deterministic Seed (`make seed`)

To satisfy repeatable simulation and evaluation benchmarks:
- `make seed` (or `python -m app.db.seed`) constructs the 4 demo stations on the 100 kVA transformer with synthetic historical sessions and 168 hours of hourly loads.
- **Idempotency Guarantee**: Running `make seed` multiple times yields identical row counts by executing a clean transactional setup with deterministic seeds.
