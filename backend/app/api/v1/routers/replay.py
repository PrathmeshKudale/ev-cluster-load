from typing import Optional
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user_optional
from app.api.v1.schemas import ReplayStartRequest, ReplayStartResponse
from app.core.errors import AppException
from app.services.replay_service import ReplayService
from app.services.user_service import UserDTO

router = APIRouter(prefix="/replay", tags=["Replay"])


@router.post("/start", response_model=ReplayStartResponse, summary="Start an accelerated 60x simulation replay")
def start_replay(
    request: ReplayStartRequest,
    current_user: Optional[UserDTO] = Depends(get_current_user_optional),
):
    """Initiate a 60x simulation replay playback session (requires operator or admin role)."""
    if current_user and current_user.role not in ("operator", "admin"):
        raise AppException(
            code="INSUFFICIENT_PERMISSIONS",
            message=f"Role '{current_user.role}' is not authorized to start simulation replay. Required: operator, admin.",
            status_code=403,
        )

    session = ReplayService.start_replay(
        speed_multiplier=request.speed_multiplier,
        horizon_hours=request.horizon_hours,
    )
    return session

