"""Smart charging recommendations router with RecommendationRepository dependency injection."""
from fastapi import APIRouter, Depends
from app.api.deps import get_recommendation_repo
from app.api.v1.schemas import RecommendRequest, RecommendResponse
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.post("", response_model=RecommendResponse, summary="Find Top-3 station and time-slot recommendations")
async def create_recommendation(
    request: RecommendRequest,
    repo: RecommendationRepository = Depends(get_recommendation_repo),
):
    """
    Generate Top-3 recommended charging slots based on user priority ('fastest', 'balanced', 'grid_friendly')
    while respecting hard transformer capacity limits (<= 90%).
    """
    top3 = RecommendationService.get_top3_recommendations(
        mode=request.mode,
        start_hour=request.start_hour,
        horizon=request.horizon,
    )
    # Persist recommendation decision in database repository (or in-memory store)
    await repo.save_recommendations(
        session_request_id="req-live",
        mode=request.mode,
        top3=top3,
    )
    return {"mode": request.mode, "top3": top3}
