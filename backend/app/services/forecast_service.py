"""Forecast service coordinating quantile forecasting and cluster load percentages."""
from typing import Dict, List, Tuple
import numpy as np

from app.core.config import STATIONS_CONFIG, TRANSFORMER_KVA, POWER_FACTOR
from app.ml.forecast import compute_forecasts


class ForecastService:
    @classmethod
    def get_cluster_and_station_forecasts(
        cls,
        stations: List[Dict] = STATIONS_CONFIG,
        transformer_kva: float = TRANSFORMER_KVA,
        power_factor: float = POWER_FACTOR,
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray], str]:
        """Compute 24-hour calibrated P10, P50, and P90 forecast bands."""
        return compute_forecasts(
            stations=stations,
            transformer_kva=transformer_kva,
            power_factor=power_factor,
        )

    @classmethod
    def format_24h_forecast(cls, start_hour: int = 14) -> Dict:
        """Format 24-hour forecast from start_hour with P10, P50, and P90 percentages."""
        cluster_pct, _, model_ver = cls.get_cluster_and_station_forecasts()
        hrs = [(start_hour + i) % 24 for i in range(24)]
        pick = lambda arr: [round(float(arr[h]) * 100.0, 1) for h in hrs]
        return {
            "hours": hrs,
            "p10": pick(cluster_pct[0]),
            "p50": pick(cluster_pct[1]),
            "p90": pick(cluster_pct[2]),
            "warn": 80,
            "critical": 90,
            "model_version": model_ver,
        }
