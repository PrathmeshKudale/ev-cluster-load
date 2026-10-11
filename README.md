# EV Cluster Load

AI-based EV charging cluster load prediction and smart charging recommendation system.

Features:
- Spatio-temporal cluster load forecasting with LightGBM core and ST-GNN topology.
- Transformer-aware dispatch with 80% warning and 90% critical limits, plus P90 early alerts.
- Calibrated P10/P50/P90 quantile intervals.
- Top-3 station and time-slot recommendations for drivers with operator grid risk monitoring.
- PostgreSQL 16 with TimescaleDB hypertables and PostGIS geospatial routing.
- Discrete-event simulation benchmarks (SimPy FCFS vs. Smart Dispatch).
- Open standards: Mock OCPP 1.6J charger and OSCP capacity endpoint.

## Architecture & Data Layers

The data architecture is split into three schemas:
1. `raw`: Immutable ingested data from external providers (ACN-Data, Open-Meteo, OCPP telemetry).
2. `clean`: Strongly typed, deduplicated, UTC timestamps, anonymized hashed user IDs (`user_hash`, no PII), and TimescaleDB hypertables (`sessions`, `station_load`, `weather`, `forecasts`).
3. `features`: Model-ready feature representations and ST-GNN graph topology (`features.station_edges`).

Documentation:
- [Database Schema & ER Diagram](docs/db/schema.md)
- [Data Modeling & Layers](docs/db/modeling.md)
- [Database Migrations & Lifecycle](docs/db/migrations.md)
- [Changelog](docs/CHANGELOG.md)

## Database Architecture, Async Repositories & Bulk Loading

The persistence layer is built on SQLAlchemy 2.0 with asynchronous execution via `asyncpg`:

- **Repository per Domain Aggregate**:
  - `ClusterRepository`: Encapsulates the Cluster aggregate (`Cluster`, `Transformer`, `Station`, `Charger`).
  - `ForecastRepository`: Manages stored 24h P10/P50/P90 quantile forecasts and `clean.station_load` telemetry.
  - `RecommendationRepository`: Persists multi-objective smart charging dispatch recommendations to `clean.recommendations`.
  - `SimulationRepository`: Tracks `clean.sim_runs` and measured `clean.sim_metrics` for FCFS vs. Smart Dispatch.
  - `UserRepository`: Handles credential verification, RBAC role lookups, and operator cluster boundaries.
- **`DEMO_MODE=memory` Zero-Database Fallback**:
  - The application operates with zero database dependencies when `DEMO_MODE=memory` (default) or when the database is offline.
  - Guarantees 100% identical response shapes across all endpoints in both in-memory demo mode and live PostgreSQL database mode.
- **Native PostgreSQL COPY Bulk Loader**:
  - High-throughput streaming via native asyncpg `copy_records_to_table` protocol for TimescaleDB hypertables (`station_load`, `forecasts`, `sessions`), with parameterized batch fallback.
- **Parameterized Query Safety**:
  - All database interactions use typed SQLAlchemy 2 `select()` statements and bound parameter mappings. Queries are never constructed from raw user input strings.

## API Architecture & Endpoints

The FastAPI backend is structured into modular layers (`api/v1`, `services`, `db`, `ml`, `sim`, `core`):

- **Interactive API Documentation**: Available at `http://localhost:8000/docs` with full OpenAPI parameter definitions and request/response examples.
- **Root Web Dashboard**: Single-page dashboard loaded at `http://localhost:8000/`.
- **Legacy Redirects**: Backward-compatible HTTP 307 redirects map `/api/*` to `/api/v1/*`.
- **Consistent Error Envelope**: All 4xx/5xx responses adhere to `{"error": {"code": "...", "message": "...", "details": ...}}`.

### Version 1 Routes (`/api/v1`)
| Method | Endpoint | Description | Auth / Scope |
|---|---|---|---|
| `POST` | `/api/v1/auth/login` | Authenticate with username & password; issues access & refresh tokens | Public |
| `POST` | `/api/v1/auth/refresh` | Rotate access & refresh tokens | Refresh Token |
| `GET` | `/api/v1/auth/me` | Current user identity, role, and cluster assignment | Bearer Token |
| `GET` | `/api/v1/clusters` | Transformer capacity (kVA), PF, and cluster station list | Public / Operator Scoped |
| `GET` | `/api/v1/clusters/{id}` | Specific cluster topology (RLS & operator boundary enforced) | Operator/Admin/Judge |
| `GET` | `/api/v1/stations` | Paginated stations list (`?page=1&page_size=10`) | Public / Operator Scoped |
| `GET` | `/api/v1/forecast` | Calibrated P10/P50/P90 load forecasts with 80%/90% limits | Public / Operator Scoped |
| `GET` | `/api/v1/transformer/{id}/risk` | Transformer risk assessment and early warning alerts | Operator Scoped |
| `GET` | `/api/v1/metrics/simulation` | Comparative metrics (FCFS vs. Smart Dispatch, peak shaving) | Operator/Admin/Judge |
| `POST` | `/api/v1/recommend` | Top-3 ranked stations and slots (`fastest`, `balanced`, `grid_friendly`) | Driver/Operator/Admin |
| `POST` | `/api/v1/replay/start` | Initialize accelerated simulation replay session | Operator / Admin |
| `WS` | `/ws/live` | Live WebSocket telemetry and event stream | Public / Live Stream |

### Recommendation & Dispatch Engine (`RecommendationService`)

The dispatch optimizer ranks stations and time slots to minimize:
$$J = w_1 \cdot \text{wait} + w_2 \cdot \text{detour} + w_3 \cdot (1 - \text{utilization balance}) + w_4 \cdot \text{overload risk}$$

- **AHP Pairwise Matrices**: Objective weights are derived from Analytic Hierarchy Process comparison matrices with Saaty consistency ratio validation ($CR < 0.10$):
  - `fastest`: Prioritizes immediate charging ($w_{\text{wait}} = 0.553, w_{\text{detour}} = 0.270, w_{\text{bal}} = 0.057, w_{\text{risk}} = 0.120$, $CR = 0.011$).
  - `balanced`: Equalized driver convenience and grid moderation ($w = [0.25, 0.25, 0.25, 0.25]$, $CR = 0.000$).
  - `grid_friendly`: Prioritizes transformer headroom and cluster load balancing ($w_{\text{wait}} = 0.065, w_{\text{detour}} = 0.098, w_{\text{bal}} = 0.354, w_{\text{risk}} = 0.483$, $CR = 0.0038$).
- **Erlang-C Queuing Model**: Computes expected queue waiting time ($W_q$) under $M/M/c$ multiserver queues given station arrival rates $\lambda$, charging duration $\mu$, and $c$ parallel chargers.
- **OR-Tools CP-SAT Batch Solver**: Resolves concurrent multi-driver arrivals (`assign_batch_drivers_cp_sat`) via integer programming, enforcing station concurrency and transformer capacity constraints.
- **Transformer Headroom Guarantee**: Verified via Hypothesis property-based testing—no recommendation pushes P90 cluster load above 90% when a feasible slot exists.

### Transformer Management & Feeder Verification (`TransformerService`)

- **Temperature Derating**: Piecewise continuous derating curve based on IEEE C57.91 and IEC 60076-7 (100% rated capacity up to 30°C, linear derate to 75% at 55°C).
- **Pandapower AC Power Flow Cross-Check**: Standalone distribution network model cross-checking transformer iron/copper losses and statutory voltage drops across 4 operating regimes (50%, 80%, 90%, 100%):
  ```bash
  python scripts/verify_feeder_pandapower.py
  ```

### Authentication & Role-Based Access Control (RBAC)

The system enforces authentication using JWT (15-minute access token, 7-day refresh token) and Argon2id password hashing.

- **Operator Isolation**: Operators can only access their assigned `cluster_id`. Cross-cluster attempts are rejected with `403 CROSS_CLUSTER_ACCESS_DENIED`. PostgreSQL Row-Level Security (RLS) is enforced via `SET LOCAL app.cluster_id = :cid`.
- **Read-Only Demo User for Judges**: A dedicated `judge` account allows full cross-cluster inspection with write protection.

| Username | Password | Role | Cluster | Description |
|---|---|---|---|---|
| `judge_demo` | `JudgeDemo2026!` | `judge` | All (Global) | Read-only evaluation account for competition judges |
| `operator_c1` | `OperatorC1_2026!` | `operator` | `C1` | Substation operator for Metro Central Cluster |
| `operator_c2` | `OperatorC2_2026!` | `operator` | `C2` | Cross-cluster operator for multi-tenant boundary tests |
| `driver_demo` | `DriverDemo2026!` | `driver` | None | EV commuter seeking slot recommendations |
| `admin_demo` | `AdminDemo2026!` | `admin` | All (Global) | Unrestricted system administrator |

## Run

### Docker Compose
Run the entire stack locally with PostgreSQL 16, TimescaleDB, PostGIS, migrations, and FastAPI:

```bash
docker compose up --build
```
Then open http://localhost:8000 for the dashboard and http://localhost:8000/docs for Swagger API documentation.

### Local Development
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements-dev.txt

# Run migrations, seed, data ingestion, and model training
make migrate
make seed
make ingest
make train

# Run test suite
make test

# Start API
cd backend && uvicorn app.main:app --reload
```

## Git Workflow
Work on `feat/...` branches, use conventional commits, keep CI green, and merge only when tests pass.
