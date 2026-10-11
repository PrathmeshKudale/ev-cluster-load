"""Clusters API router with ClusterRepository aggregate dependency injection."""
from typing import Optional
from fastapi import APIRouter, Depends, Path

from app.api.deps import (
    get_cluster_repo,
    get_current_user_optional,
    verify_async_cluster_access,
)
from app.api.v1.schemas import ClusterResponse
from app.db.repositories.cluster_repository import ClusterRepository
from app.services.user_service import UserDTO

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("", response_model=ClusterResponse, summary="Get cluster topology and transformer parameters")
async def get_clusters(
    current_user: Optional[UserDTO] = Depends(get_current_user_optional),
    repo: ClusterRepository = Depends(get_cluster_repo),
):
    """Retrieve electrical parameters, transformer rating, and connected stations for the cluster."""
    cluster_id = "C1"
    if current_user and current_user.role == "operator" and current_user.cluster_id:
        cluster_id = current_user.cluster_id
        await verify_async_cluster_access(cluster_id, user=current_user, session=repo.session)

    return await repo.get_cluster_topology(cluster_id)


@router.get("/{id}", response_model=ClusterResponse, summary="Get specific cluster by identifier with RBAC scoping")
async def get_cluster_by_id(
    id: str = Path(..., examples=["C1"], description="Cluster identifier"),
    current_user: Optional[UserDTO] = Depends(get_current_user_optional),
    repo: ClusterRepository = Depends(get_cluster_repo),
):
    """Retrieve cluster by ID, enforcing operator cluster boundary."""
    await verify_async_cluster_access(id, user=current_user, session=repo.session)
    return await repo.get_cluster_topology(id)
