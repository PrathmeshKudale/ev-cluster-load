"""Clusters API router."""
from fastapi import APIRouter
from app.core.config import TRANSFORMER_KVA, POWER_FACTOR, STATIONS_CONFIG
from app.api.v1.schemas import ClusterResponse

router = APIRouter(prefix="/clusters", tags=["Clusters"])


@router.get("", response_model=ClusterResponse, summary="Get cluster topology and transformer parameters")
def get_clusters():
    """Retrieve electrical parameters, transformer rating, and connected stations for the cluster."""
    return {
        "transformer_kva": TRANSFORMER_KVA,
        "power_factor": POWER_FACTOR,
        "stations": STATIONS_CONFIG,
    }
