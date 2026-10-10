# EV Cluster Load

Prototype of an AI-based EV cluster load prediction and smart charging recommendation system.
It is the walking skeleton of the master plan: demo data, a P10/P50/P90 forecast, transformer risk,
Top-3 station and slot recommendations, and an operator dashboard.

## Run

Docker: `docker compose up --build`, then open http://localhost:8000

Local:

    python -m venv .venv && source .venv/bin/activate
    pip install -r backend/requirements-dev.txt
    cd backend && python -m pytest -q
    uvicorn app.main:app --reload

API docs are at http://localhost:8000/docs

## Layout

- `backend/app/main.py`: FastAPI app with forecast, transformer monitor (80% warning, 90% critical), M/M/c wait model and scoring
- `backend/tests/`: pytest checks (quantile order, wait model, transformer constraint)
- `frontend/index.html`: single-file dashboard served by the API
- `.github/workflows/ci.yml`: runs the tests on every push and pull request

## Placeholders to replace

- Demo history is synthetic and seeded (`_history`). Swap in ACN-Data or UrbanEV.
- Forecast bands are hour-of-day percentiles (`_bands`). Swap in LightGBM quantile models and a backtest.
- Nothing in this repo is a measured result. Headline numbers must come from the SimPy FCFS vs smart-dispatch simulation.

## Next steps

1. Data ingest (ACN-Data, Open-Meteo) into PostgreSQL + TimescaleDB
2. LightGBM quantile forecast with rolling-origin backtest and conformal calibration
3. SimPy simulation: first-come-first-served vs smart dispatch
4. React + Vite frontend with Leaflet map, then OCPP mock charger and OSCP-style endpoint

## Git workflow

Work on `feat/...` branches, open pull requests into `main`, use conventional commits, and merge only when CI passes.
