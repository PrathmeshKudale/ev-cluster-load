# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-13

### Added - feat/z4-release
- **Final Quality Assurance & Release Validation**:
  - Validated full automated test suite across backend (117 tests passing) and frontend (46 tests passing, zero failures).
  - Executed complete database restore drill (`scripts/restore_drill.py`) verifying migration schema setup and 100% identical row counts across idempotent seed executions.
  - Executed end-to-end machine learning and simulation lifecycle (`make ingest` -> `make train` -> `make simulate` -> `make results`).
  - Built optimized client bundle and validated offline demo mode (`make demo`) operating with zero database or external network requirements.
  - Tagged production release `v1.0.0`.

### Added - feat/z3-docs
- **README Rewrite with Mermaid Architecture & Evidence Links**:
  - Rewrote project `README.md` featuring top-line measured results table, Mermaid architecture diagram, 3-command quick start (`make setup`, `make up`, `make demo`), and API overview.
  - Linked every empirical claim to its backing test, script, or reproducible simulation summary in `results/`.
- **System Architecture Deep-Dive (`docs/architecture.md`)**:
  - Created comprehensive architectural guide detailing standards ingestion, AI pipeline, multi-objective optimization, and TimescaleDB persistence layers.
- **Empirical Results Report & Generator (`docs/results.md`, `scripts/generate_results_md.py`)**:
  - Implemented `scripts/generate_results_md.py` generating `docs/results.md` directly from `results/sim_summary.json`, `results/backtest.csv`, and `results/ablation.csv`.
  - Added `make results` target to `Makefile`.
- **One-Page Executive Brief (`docs/pitch.md`)**:
  - Structured crisp one-page pitch outlining problem statement, solution mechanics, measured performance numbers, and strategic roadmap.

### Added - feat/z2-standards
- **OCPP 1.6J Central System & WebSocket Server**:
  - Implemented OCPP 1.6 JSON-over-WebSocket protocol handler under `/ocpp/{charger_id}` and `/api/v1/ocpp/{charger_id}` with `subprotocols=["ocpp1.6"]`.
  - Full Core Profile support for `BootNotification`, `StatusNotification`, `StartTransaction`, `MeterValues`, and `StopTransaction`.
  - Transaction lifecycle tracking, energy delivery calculation (`kWh`), and live power load metrics stored in `OcppService` with safe database persistence.
  - Endpoints `GET /sessions` and `GET /api/v1/sessions` for operator dashboard and session audits.
  - Endpoints `GET /standards/chargers` and `GET /standards/alerts` for real-time charge point monitoring.
- **Python `ocpp` Mock Charger Client (`MockChargerClient`)**:
  - Implemented `MockChargerClient` in `backend/app/services/mock_charger.py` subclassing `ocpp.v16.ChargePoint`.
  - Created standalone CLI runner `scripts/mock_charger.py` to simulate realistic full charging sessions against running Central Systems.
- **OSCP 2.0 Dynamic DSO Capacity Limits & Overload Alerting**:
  - Implemented `PUT /oscp/capacity-forecast` (and `/api/v1/oscp/capacity-forecast`) allowing Distribution System Operators (DSOs) to push time-varying capacity limits.
  - Sub-tick grid protection: Compares DSO limit against active cluster load ($\text{kW} / 0.95$). If limit drops below active load, an overload alert (`ALT-OSCP-*`) fires within one tick.
  - Integrated into `TransformerService.get_transformer_risk()` and `ReplayService.get_full_frame_at_tick()` to transition risk level to `critical` dynamically.
- **Open Standards Documentation & Test Suite**:
  - Created comprehensive documentation in `docs/standards.md` detailing message schemas, parameters, and verification.
  - Created automated test suite in `backend/tests/test_standards.py` covering the 5-message OCPP lifecycle, WebSocket framing, OSCP forecast limit changes, and instantaneous overload alerting.

### Added - feat/z1-replay-shap
- **WebSocket Replay Engine (1x up to 1440x)**:
  - Implemented accelerated day simulation replay streaming on `/ws/replay` and `/api/v1/ws/replay` in `backend/app/api/v1/routers/websockets.py`.
  - ReplayService generates complete 1440-minute simulated day frames (1 tick = 1 minute) at speeds up to 1440x (a full 24h day finishes in ~60 seconds).
  - Streams dynamic cluster demand, per-station bay occupancies, Erlang-C queue delay times, 80% warn / 90% crit threshold alerts, and dynamic recommendations.
  - Interactive WebSocket controls supporting `start`, `pause`, `resume`, `seek`, `speed`, and `stop`.
- **SHAP TreeExplainer for LightGBM Quantile Forecast**:
  - Implemented `ShapExplainer` in `backend/app/ml/shap_explainer.py` wrapping `shap.TreeExplainer` on the trained LightGBM quantile regression model.
  - Extracts exact feature attributions for input features (`hour`, `temperature`, `lag_1h`, `rolling_mean_4h`, `chargers_available`, `active_sessions`).
  - Attached top-3 SHAP attribution reasons to every candidate recommendation in `RecommendationService.get_top3_recommendations()`.
- **Frontend Live Replay Dashboard & Explainability Why Drawer**:
  - Updated `ReplayControls` to support 1440x playback speed with intuitive timeline scrubber.
  - Revamped `ReplayPage` with real-time transformer loading telemetry meter, dynamic active alerts feed, hub queue congestion monitor, and tick-by-tick recommendation updates.
  - Added "LightGBM TreeExplainer (Top 3 SHAP Attributions)" section into `RecommendationCard` Why Drawer displaying real model reasons alongside queue wait, detour, and overload risk.
- **Verification & Acceptance Test Suite**:
  - Added `backend/tests/test_replay_shap.py` testing TreeExplainer initialization, SHAP feature rankings, 1440x replay frame generation, and `/ws/replay` WebSocket streaming.
  - Added `frontend/src/features/recommend/__tests__/WhyDrawerShap.test.tsx` verifying Why Drawer opens and renders real TreeSHAP output.

### Added - feat/b4-db
- **SQLAlchemy 2 Async with asyncpg Engine**:
  - Implemented async engine (`async_engine`) and session factory (`AsyncSessionLocal`) using `postgresql+asyncpg://` in `backend/app/db/connection.py`.
  - Added FastAPI async session dependencies: `get_async_db` and `get_async_db_optional` with transaction management (automatic commit and rollback on exception).
  - Provided `set_async_db_cluster_id` and `verify_async_cluster_access` to preserve PostgreSQL Row-Level Security (RLS) across async routes.
- **Repository Pattern per Domain Aggregate**:
  - Structured modular aggregate repositories under `backend/app/db/repositories/`:
    - `ClusterRepository`: Manages Cluster, Transformer, Station, and Charger aggregates; queries cluster topology and paginated station listings.
    - `ForecastRepository`: Manages Forecast, StationLoad, and Weather aggregates; queries and formats stored 24h P10/P50/P90 calibrated load forecasts.
    - `RecommendationRepository`: Persists smart dispatch decisions and candidate slot recommendations to `clean.recommendations`.
    - `SimulationRepository`: Queries and persists measured simulation benchmark runs and metrics (`SimRun`, `SimMetric`).
    - `UserRepository`: Manages User aggregate entities, credential lookups, and RBAC roles.
- **`DEMO_MODE=memory` Zero-Database Fallback**:
  - Integrated `DEMO_MODE` environment switch (`memory` by default).
  - Enables full application functionality without requiring a running database while guaranteeing 100% exact response shape parity between memory demo mode and database mode.
- **Native COPY-Based Bulk Loader (`CopyBulkLoader`)**:
  - Implemented high-throughput bulk ingestion via native asyncpg `copy_records_to_table` protocol for `clean.station_load`, `clean.forecasts`, and `clean.sessions`, with parameterized batch fallback.
- **Strict Parameterized Query Safety**:
  - Ensured all queries use typed SQLAlchemy 2 `select()` and bound parameters (`:param`). Never builds SQL queries from user input.
- **Acceptance & Container Test Suite**:
  - Added comprehensive test suite in `backend/tests/test_db_integration.py` verifying shape parity, repository operations, SQL injection safety, and execution against live PostgreSQL/TimescaleDB container in CI.

### Added - feat/b3-logic
- **Pure Unit-Testable Domain Services**:
  - `RecommendationService` (`backend/app/services/recommendation_service.py`):
    - Multi-objective dispatch score minimizing:
      $$J = w_1 \cdot \text{wait} + w_2 \cdot \text{detour} + w_3 \cdot (1 - \text{utilization balance}) + w_4 \cdot \text{overload risk}$$
    - Analytic Hierarchy Process (AHP) pairwise comparison matrices with Saaty consistency check ($CR < 0.10$) for 3 driver modes: `fastest` ($CR=0.011$), `balanced` ($CR=0.000$), and `grid_friendly` ($CR=0.0038$).
    - Erlang-C ($M/M/c$) queuing model computing expected wait time in minutes given arrival rate $\lambda$, service rate $\mu$, and $c$ parallel charging bays.
    - Google OR-Tools CP-SAT integer programming solver (`assign_batch_drivers_cp_sat`) for multi-driver batch arrivals subject to station bay capacity and cluster transformer kVA limits.
    - Transformer load constraint: Zero recommendations exceed 90% effective transformer loading when a feasible slot is available.
  - `TransformerService` (`backend/app/services/transformer_service.py`):
    - Pure conversions: active power (kW) to apparent power (kVA) using power factor ($\text{kVA} = \text{kW} / \text{pf}$), and vice versa.
    - Continuous piecewise ambient-temperature derating based on IEEE C57.91 and IEC 60076-7 loading guides (full capacity up to 30°C, linear derate up to 55°C).
    - Pandapower distribution feeder integration (`cross_check_feeder_pandapower`) modeling 11/0.415 kV substation, radial underground aluminum lines, and transformer losses.
  - `FairnessService` (`backend/app/services/fairness_service.py`):
    - Jain's Fairness Index ($\mathcal{J} \in [1/n, 1]$), station utilization balance, and peak-shaving comparative metrics between FCFS and Smart Dispatch.
  - `ReplayService` (`backend/app/services/replay_service.py`):
    - Pure simulation playback engine supporting `start_replay`, `tick`, `seek`, `pause`, `resume`, `stop`, and telemetry state generation with ISO timestamps.
- **Feeder Verification Script**:
  - Added `scripts/verify_feeder_pandapower.py` executing standalone AC power flow across 50%, 80%, 90%, and 100% feeder load regimes, validating transformer loss and voltage drops against statutory limits.
- **Acceptance & Hypothesis Property-Based Testing**:
  - Implemented Hypothesis property-based testing in `backend/tests/test_logic.py` proving that no recommendation pushes P90 cluster load above 90% when a feasible slot exists.
  - Added comprehensive test suites for AHP Consistency Ratios, Erlang-C queuing, CP-SAT batch assignment, and Pandapower AC power flow convergence.

### Added - feat/b2-auth
- **JWT Authentication & Token Lifecycle**:
  - Implemented short-lived access tokens (15 minutes) and longer-lived refresh tokens (7 days) in `backend/app/core/security.py`.
  - Added token rotation and decoding with dedicated exception handling for `TOKEN_EXPIRED` (401) and `INVALID_TOKEN` (401).
  - Auth endpoints under `/api/v1/auth`: `POST /login`, `POST /refresh`, and `GET /me`.
- **Argon2id Password Hashing**:
  - Replaced legacy hashing with state-of-the-art Argon2id password hasher (`argon2-cffi`) resistant to GPU cracking and side-channel attacks.
- **Role-Based Access Control (RBAC)**:
  - Added user roles: `driver`, `operator`, `admin`, and read-only `judge` demo user.
  - Role enforcement on sensitive endpoints (e.g. simulation replay restricted to `operator` and `admin`, returning 403 `INSUFFICIENT_PERMISSIONS` for drivers and judges).
- **Cluster Scoping & PostgreSQL Row-Level Security (RLS)**:
  - Enforced in API: Operators can only access their assigned `cluster_id`, raising 403 `CROSS_CLUSTER_ACCESS_DENIED` on cross-cluster requests.
  - Enforced in Database: Implemented PostgreSQL Row-Level Security (RLS) on `clean.stations`, `clean.transformers`, and `clean.clusters` driven by session parameter `app.cluster_id`.
  - Helper `set_db_cluster_id()` applies `SET LOCAL app.cluster_id = :cid` during operator requests.
- **Alembic Migration `0002_add_auth_and_user_roles.py`**:
  - Fully reversible migration adding `username`, `email`, `hashed_password`, `role`, `cluster_id`, and `is_active` to `clean.users`.
  - Added unique indexes and RLS policies on cluster tables with full downgrade support.
- **Seeded Demo Accounts**:
  - Seeded read-only demo user `judge_demo` for judges (`JudgeDemo2026!`) with unrestricted read access across all clusters.
  - Seeded demo operator accounts (`operator_c1`, `operator_c2`), driver (`driver_demo`), and administrator (`admin_demo`).
- **Security & Secret Hygiene**:
  - Created `.env.example` templates; verified no live secrets, credentials, or `.env` files are tracked in git.
  - Comprehensive 18-test suite in `backend/tests/test_auth.py` covering login, refresh, expired tokens, role violations, cross-cluster access, and git secret audits.

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
