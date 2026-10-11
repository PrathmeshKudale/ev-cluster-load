"""Aggregates repositories package for EV Cluster Load domain."""
from app.db.repositories.base import BaseRepository
from app.db.repositories.cluster_repository import ClusterRepository
from app.db.repositories.forecast_repository import ForecastRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.simulation_repository import SimulationRepository
from app.db.repositories.user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "ClusterRepository",
    "ForecastRepository",
    "RecommendationRepository",
    "SimulationRepository",
    "UserRepository",
]
