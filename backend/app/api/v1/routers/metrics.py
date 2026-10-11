"""Simulation metrics API router with SimulationRepository dependency injection."""
from fastapi import APIRouter, Depends
from app.api.deps import get_simulation_repo
from app.db.repositories.simulation_repository import SimulationRepository

router = APIRouter(prefix="/metrics", tags=["Simulation"])


@router.get("/simulation", summary="Get measured simulation benchmark metrics comparing FCFS vs Smart Dispatch")
async def get_simulation_metrics(
    repo: SimulationRepository = Depends(get_simulation_repo),
):
    """Retrieve measured peak shaving, waiting time reduction, and fairness metrics from simulation benchmarks."""
    return await repo.get_simulation_metrics()
