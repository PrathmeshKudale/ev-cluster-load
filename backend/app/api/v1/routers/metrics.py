"""Simulation metrics API router."""
from fastapi import APIRouter
from app.services.simulation_service import SimulationService

router = APIRouter(prefix="/metrics", tags=["Simulation"])


@router.get("/simulation", summary="Get measured simulation benchmark metrics comparing FCFS vs Smart Dispatch")
def get_simulation_metrics():
    """Retrieve measured peak shaving, waiting time reduction, and fairness metrics from simulation benchmarks."""
    return SimulationService.get_simulation_metrics()
