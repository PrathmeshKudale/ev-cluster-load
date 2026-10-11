from typing import Optional
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, verify_cluster_access
from app.api.v1.schemas import TransformerRiskResponse
from app.db.connection import get_db
from app.services.transformer_service import TransformerService
from app.services.user_service import UserDTO

router = APIRouter(prefix="/transformer", tags=["Transformer"])


@router.get("/{id}/risk", response_model=TransformerRiskResponse, summary="Get transformer risk assessment and early warning alerts")
def get_transformer_risk(
    id: str = Path(..., examples=["T1"], description="Transformer identifier"),
    start_hour: int = Query(14, ge=0, le=23, description="Starting hour of day"),
    current_user: Optional[UserDTO] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Monitor transformer load risk, warning (80%) and critical (90%) thresholds, and peak hours."""
    # Transformer T1 belongs to cluster C1
    cluster_id = "C1" if id.startswith("T1") or id == "T1" else id
    verify_cluster_access(cluster_id, user=current_user, db=db)
    return TransformerService.get_transformer_risk(transformer_id=id, start_hour=start_hour)

