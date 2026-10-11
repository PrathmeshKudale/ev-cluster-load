"""Transformer monitoring router."""
from fastapi import APIRouter, Path, Query
from app.services.transformer_service import TransformerService
from app.api.v1.schemas import TransformerRiskResponse

router = APIRouter(prefix="/transformer", tags=["Transformer"])


@router.get("/{id}/risk", response_model=TransformerRiskResponse, summary="Get transformer risk assessment and early warning alerts")
def get_transformer_risk(
    id: str = Path(..., examples=["T1"], description="Transformer identifier"),
    start_hour: int = Query(14, ge=0, le=23, description="Starting hour of day"),
):
    """Monitor transformer load risk, warning (80%) and critical (90%) thresholds, and peak hours."""
    return TransformerService.get_transformer_risk(transformer_id=id, start_hour=start_hour)
