"""Clusters API router."""
from typing import Optional
from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, verify_cluster_access
from app.api.v1.schemas import ClusterResponse
from app.core.config import POWER_FACTOR, STATIONS_CONFIG, TRANSFORMER_KVA
from app.db.connection import get_db
from app.services.user_service import UserDTO

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("", response_model=ClusterResponse, summary="Get cluster topology and transformer parameters")
def get_clusters(
    current_user: Optional[UserDTO] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve electrical parameters, transformer rating, and connected stations for the cluster."""
    # If operator, ensure RLS and cluster scoping are active
    if current_user and current_user.role == "operator" and current_user.cluster_id:
        verify_cluster_access(current_user.cluster_id, user=current_user, db=db)

    return {
        "transformer_kva": TRANSFORMER_KVA,
        "power_factor": POWER_FACTOR,
        "stations": STATIONS_CONFIG,
    }


@router.get("/{id}", response_model=ClusterResponse, summary="Get specific cluster by identifier with RBAC scoping")
def get_cluster_by_id(
    id: str = Path(..., examples=["C1"], description="Cluster identifier"),
    current_user: Optional[UserDTO] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Retrieve cluster by ID, enforcing operator cluster boundary."""
    verify_cluster_access(id, user=current_user, db=db)
    return {
        "transformer_kva": TRANSFORMER_KVA,
        "power_factor": POWER_FACTOR,
        "stations": STATIONS_CONFIG,
    }

