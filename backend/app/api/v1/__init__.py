"""API v1 router assembly."""
from fastapi import APIRouter
from app.api.v1.routers.clusters import router as clusters_router
from app.api.v1.routers.stations import router as stations_router
from app.api.v1.routers.forecast import router as forecast_router
from app.api.v1.routers.transformer import router as transformer_router
from app.api.v1.routers.metrics import router as metrics_router
from app.api.v1.routers.recommendations import router as recommendations_router
from app.api.v1.routers.replay import router as replay_router
from app.api.v1.routers.websockets import router as ws_router
from app.api.v1.routers.auth import router as auth_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(clusters_router)
api_v1_router.include_router(stations_router)
api_v1_router.include_router(forecast_router)
api_v1_router.include_router(transformer_router)
api_v1_router.include_router(metrics_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(replay_router)
api_v1_router.include_router(ws_router)

__all__ = ["api_v1_router"]
