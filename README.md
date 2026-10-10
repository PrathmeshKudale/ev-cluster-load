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

# Run migrations and seed demo cluster
make migrate
make seed

# Run test suite
make test

# Start API
cd backend && uvicorn app.main:app --reload
```

## Git Workflow
Work on `feat/...` branches, use conventional commits, keep CI green, and merge only when tests pass.
