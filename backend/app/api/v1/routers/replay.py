"""Simulation replay control router."""
from fastapi import APIRouter
from app.services.simulation_service import ReplayService
from app.api.v1.schemas import ReplayStartRequest, ReplayStartResponse

router = APIRouter(prefix="/replay", tags=["Replay"])


@router.post("/start", response_model=ReplayStartResponse, summary="Start an accelerated 60x simulation replay")
def start_replay(request: ReplayStartRequest):
    """Initiate a 60x simulation replay playback session."""
    session = ReplayService.start_replay(
        speed_multiplier=request.speed_multiplier,
        horizon_hours=request.horizon_hours,
    )
    return session
