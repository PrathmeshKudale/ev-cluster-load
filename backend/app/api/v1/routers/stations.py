"""Stations API router with ClusterRepository dependency injection and pagination."""
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_cluster_repo
from app.api.v1.schemas import StationSchema
from app.core.pagination import PaginatedResponse
from app.db.repositories.cluster_repository import ClusterRepository

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("", response_model=PaginatedResponse[StationSchema], summary="List charging stations in the cluster")
async def list_stations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    repo: ClusterRepository = Depends(get_cluster_repo),
):
    """Retrieve paginated list of charging stations connected to the cluster."""
    items, total_items = await repo.list_stations(page=page, page_size=page_size)

    return PaginatedResponse.create(
        items=items,
        page=page,
        page_size=page_size,
        total_items=total_items,
    )
