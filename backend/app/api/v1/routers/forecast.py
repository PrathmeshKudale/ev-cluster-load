"""Forecast API router."""
from fastapi import APIRouter, Query
from app.services.forecast_service import ForecastService
from app.api.v1.schemas import ForecastResponse

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("", response_model=ForecastResponse, summary="Get 24-hour calibrated quantile load forecast")
def get_forecast(
    start_hour: int = Query(14, ge=0, le=23, description="Starting hour of day for forecast (0-23)")
):
    """Retrieve 24-hour P10, P50, and P90 calibrated cluster load forecasts."""
    return ForecastService.format_24h_forecast(start_hour=start_hour)
