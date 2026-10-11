"""Smart charging recommendations router."""
from fastapi import APIRouter
from app.services.recommendation_service import RecommendationService
from app.api.v1.schemas import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/recommend", tags=["Recommendations"])


@router.post("", response_model=RecommendResponse, summary="Find Top-3 station and time-slot recommendations")
def create_recommendation(request: RecommendRequest):
    """
    Generate Top-3 recommended charging slots based on user priority ('fastest', 'balanced', 'grid_friendly')
    while respecting hard transformer capacity limits (<= 90%).
    """
    top3 = RecommendationService.get_top3_recommendations(
        mode=request.mode,
        start_hour=request.start_hour,
        horizon=request.horizon,
    )
    return {"mode": request.mode, "top3": top3}
