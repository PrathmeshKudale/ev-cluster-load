# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added - feat/b1-api
- Restructured `backend/app` into modular layered architecture:
  - `app/api/v1/`: Versioned API routers (`clusters`, `stations`, `forecast`, `transformer`, `metrics`, `recommendations`, `replay`, `websockets`) and OpenAPI schemas.
  - `app/services/`: Decoupled business logic (`ForecastService`, `TransformerService`, `RecommendationService`, `SimulationService`).
  - `app/core/`: Application settings, standard error envelope (`ErrorEnvelope`), exception handlers, and reusable pagination model (`PaginatedResponse`).
  - `app/sim/`: Discrete-event simulation runner framework (`DiscreteEventEngine`).
  - `app/db/`: Database models, engine session, and idempotent seeder.
  - `app/ml/`: Feature engineering, model training, and inference forecasting modules.
- Endpoints served under `/api/v1`:
  - `GET /api/v1/clusters`: Cluster metadata, transformer rating (kVA), and stations.
  - `GET /api/v1/stations`: Paginated charging station listing with per-charger kW, count, and detour.
  - `GET /api/v1/forecast`: Calibrated 24h P10/P50/P90 load forecasts against 80%/90% limits.
  - `GET /api/v1/transformer/{id}/risk`: Transformer risk evaluation and early warning alert indicators.
  - `GET /api/v1/metrics/simulation`: Performance and peak-shaving comparison (Smart Dispatch vs. FCFS).
  - `POST /api/v1/recommend`: Top-3 ranked station and slot recommendations across `fastest`, `balanced`, and `grid_friendly` modes.
  - `POST /api/v1/replay/start`: Accelerated replay session initialization.
  - `WS /ws/live`: Live telemetry and interactive dispatch WebSocket streaming.
- Legacy backward compatibility:
  - Preserved existing `/api/cluster`, `/api/stations`, `/api/forecast`, `/api/transformer`, and `/api/recommend` endpoints via HTTP 307 temporary redirects to ensure the single-page dashboard (`frontend/index.html`) operates without modification.
- Robust API standards:
  - Consistent error envelope (`{"error": {"code": ..., "message": ..., "details": ...}}`) for 400, 404, 422, and 500 status codes.
  - OpenAPI tags and examples documented on every route and schema for interactive testing via `/docs`.
- Test suite:
  - Added comprehensive contract test suite in `backend/tests/test_contract.py` covering all routes, pagination, OpenAPI schema compliance, legacy redirects, error envelopes, and WebSocket streaming.

### Added - feat/m3-lightgbm
- Feature engineering pipeline in `backend/app/ml/features.py`:
  - Temporal features: hour of day, day of week, weekend/holiday indicator.
  - Weather features: ambient temperature and rain precipitation.
  - Lag features: active load at 1h, 24h, and 168h (1 week).
  - Rolling windows: 4-hour and 24-hour moving averages.
  - Operational features: chargers available and concurrent active sessions.
- Multi-quantile LightGBM training (`backend/app/ml/train.py`):
  - Trained quantile regressors for P10, P50, and P90 with pinball loss objectives.
  - Asymmetric split-conformal calibration on held-out validation set to guarantee empirical coverage reaches $\ge 80\%$ on out-of-sample data.
  - Local MLflow experiment tracking logging parameters, metrics, and serialized model artifacts.
  - Out-of-sample rolling backtest comparing against Seasonal Naive baseline, achieving **67.8% MAE improvement** and **82.9% P10–P90 empirical coverage** recorded in `results/backtest.csv`.
- Integrated forecast module (`backend/app/ml/forecast.py`) replacing synthetic hour-of-day percentile bands in `backend/app/main.py`:
  - Retains identical shape `(3, 24)` and non-negativity/monotonicity constraints.
  - Automatically falls back to Seasonal Naive if model artifact is unavailable.
- Added `make train` target in root `Makefile`.
- Added unit and regression tests in `backend/tests/test_forecast.py`.

### Added - feat/m1-ingest
- Ingestion adapters under `backend/app/ml/data/`:
  - `acn_adapter`: ACN-Data API fetch with `.env` token support, fallback to deterministic synthetic sessions, SHA-256 user ID anonymization, and splitting of a single site into 4 virtual stations (`is_synthetic = True`).
  - `urban_ev_adapter`: UrbanEV fast-charging session adapter with synthetic fallback.
  - `weather_adapter`: Open-Meteo hourly weather client (zero API key needed) with diurnal offline fallback.
  - `aggregator`: Hourly station load aggregation computing active kW, active chargers, and utilization rate with missing hours detection and coverage reporting.
  - `copy_loader`: Fast PostgreSQL bulk `COPY FROM STDIN` loader with offline CSV buffer fallback.
  - `eda`: Exploratory data analysis plotting generating `hourly_load_profiles.png`, `session_duration_energy.png`, and `weather_correlation.png` into `docs/img/`.
  - `ingest`: Orchestrator runner with CLI reporting table for station coverage and row counts (`make ingest`).
- Added `make ingest` target to root `Makefile`.
- Added unit and integration test suite `backend/tests/test_ingest.py`.

### Added - feat/d9-migrations
- Explicit Alembic and SQLAlchemy constraint naming conventions (`ix_`, `uq_`, `ck_`, `fk_`, `pk_`).
- Timestamped Alembic revision file naming template.
- Verified reversible migration downgrades (`alembic downgrade base`).
- Strict separation of schema DDL from seed data (`make migrate` vs `make seed`).
- Comprehensive GitHub Actions CI workflow applying migrations to blank DB, running upgrade/downgrade/upgrade cycle, seeding, and applying migrations to seeded DB.
- Comprehensive documentation in `docs/db/migrations.md` detailing the migration lifecycle and the Expand-then-Contract zero-downtime evolution pattern.

### Added - feat/d3-modeling
- Multi-schema PostgreSQL 16 architecture with `raw`, `clean`, and `features` schemas.
- TimescaleDB hypertables for `clean.sessions`, `clean.station_load`, `clean.weather`, and `clean.forecasts`.
- PostGIS geometry support for spatial station coordinates.
- Spatial-Temporal GNN graph edges table (`features.station_edges`) populated via OSRM routing with graceful Haversine fallback.
- Externalized configuration tables for transformer parameters (`clean.config_transformer`), IEEE/IEC thermal derating (`clean.config_derating_curve`), and Indian Time-of-Day tariffs (`clean.config_tod_tariff`).
- Deterministic idempotent seeder (`make seed` / `python -m app.db.seed`) generating the 4-station demo cluster on a 100 kVA transformer.
- Documentation for database ER diagram (`docs/db/schema.md`) and modeling layers (`docs/db/modeling.md`).
- Root `Makefile` with targets: `seed`, `migrate`, `migrate-down`, `migrate-check`, `test`, `up`, `down`.
