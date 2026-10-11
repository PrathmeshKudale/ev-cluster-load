"""Forecast API router with ForecastRepository dependency injection."""
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_forecast_repo
from app.api.v1.schemas import ForecastResponse
from app.db.repositories.forecast_repository import ForecastRepository

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("", response_model=ForecastResponse, summary="Get 24-hour calibrated quantile load forecast")
async def get_forecast(
    start_hour: int = Query(14, ge=0, le=23, description="Starting hour of day for forecast (0-23)"),
    repo: ForecastRepository = Depends(get_forecast_repo),
):
    """Retrieve 24-hour P10, P50, and P90 calibrated cluster load forecasts."""
    return await repo.get_24h_forecast(cluster_id="C1", start_hour=start_hour)
