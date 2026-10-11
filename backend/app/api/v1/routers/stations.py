"""Stations API router with pagination."""
from fastapi import APIRouter, Query
from app.core.config import STATIONS_CONFIG
from app.core.pagination import PaginatedResponse
from app.api.v1.schemas import StationSchema

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=PaginatedResponse[StationSchema], summary="List charging stations in the cluster")
def list_stations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """Retrieve paginated list of charging stations connected to the cluster."""
    total_items = len(STATIONS_CONFIG)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    items = STATIONS_CONFIG[start_idx:end_idx]

    return PaginatedResponse.create(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
    )
