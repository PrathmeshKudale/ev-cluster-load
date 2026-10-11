"""EV Cluster Load FastAPI application serving /api/v1 with legacy redirects and static dashboard."""
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core import (
    TRANSFORMER_KVA,
    POWER_FACTOR as PF,
    WARN_THRESHOLD as WARN,
    CRIT_THRESHOLD as CRIT,
    SESSION_HOURS as SESSION_H,
    STATIONS_CONFIG as STATIONS,
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.services import (
    ForecastService,
    TransformerService,
    RecommendationService,
    erlang_c_wait_min,
)
from app.api.v1 import api_v1_router
from app.api.v1.routers.websockets import router as ws_router

# Backward compatibility exports for existing modules & tests
CLUSTER_PCT, STATION_UTIL, MODEL_VERSION = ForecastService.get_cluster_and_station_forecasts()
level = TransformerService.level

TAGS_METADATA = [
    {"name": "Clusters", "description": "Cluster topology, transformer capacity, and connected stations"},
    {"name": "Stations", "description": "Charging stations with pagination and charger capacities"},
    {"name": "Forecast", "description": "Calibrated P10/P50/P90 quantile load predictions"},
    {"name": "Transformer", "description": "Transformer risk monitoring and early warning alerts (80% warn, 90% crit)"},
    {"name": "Recommendations", "description": "Multi-objective smart charging dispatch recommendations"},
    {"name": "Simulation", "description": "Measured discrete-event simulation benchmarks (FCFS vs Smart Dispatch)"},
    {"name": "Replay", "description": "Accelerated 60x historical and simulated replay control"},
    {"name": "Live Telemetry", "description": "Real-time WebSocket streaming of cluster metrics"},
]

app = FastAPI(
    title="EV Cluster Load API",
    version="1.0.0",
    description="AI-based EV cluster load prediction and smart charging recommendation system.",
    openapi_tags=TAGS_METADATA,
)

# Exception handlers for consistent error envelopes
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Include v1 API routes under /api/v1
app.include_router(api_v1_router)

# Mount root WebSocket route /ws/live alongside /api/v1/ws/live
app.include_router(ws_router)


# ==============================================================================
# Legacy /api Routes Redirects (307 Temporary Redirect preserving HTTP methods)
# ==============================================================================

@app.get("/api/health", tags=["Health"], summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/api/v1/health", tags=["Health"], summary="Health check (v1)")
def health_v1():
    return {"status": "ok"}


@app.get("/api/cluster", include_in_schema=False)
def legacy_cluster():
    return RedirectResponse(url="/api/v1/clusters", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/api/stations", include_in_schema=False)
def legacy_stations(request: Request):
    query_str = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/api/v1/stations{query_str}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/api/forecast", include_in_schema=False)
def legacy_forecast(request: Request):
    query_str = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/api/v1/forecast{query_str}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/api/transformer", include_in_schema=False)
def legacy_transformer(request: Request):
    query_str = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(url=f"/api/v1/transformer/T1/risk{query_str}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.post("/api/recommend", include_in_schema=False)
def legacy_recommend():
    return RedirectResponse(url="/api/v1/recommend", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


# Mount static frontend dashboard
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True), name="ui")
