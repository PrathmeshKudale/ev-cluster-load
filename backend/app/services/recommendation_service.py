"""Smart charging recommendation service with Erlang-C queuing and transformer constraint."""
from typing import Dict, List
import numpy as np

from app.core.config import (
    STATIONS_CONFIG,
    SESSION_HOURS,
    WARN_THRESHOLD,
    CRIT_THRESHOLD,
    DELAY_WEIGHT,
    RECOMMENDATION_MODES,
)
from app.services.forecast_service import ForecastService


def erlang_c_wait_min(c: int, util: float, session_h: float = SESSION_HOURS) -> float:
    """Mean queue wait time in minutes for an M/M/c charging site with c chargers."""
    a = min(util, 0.995) * c
    term, total = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        total += term
    top = term * a / c / (1.0 - a / c)
    wait_hours = (top / (total + top)) * session_h / max(c - a, 0.01)
    return float(min(wait_hours * 60.0, 90.0))


class RecommendationService:
    @classmethod
    def get_top3_recommendations(
        cls,
        mode: str = "balanced",
        start_hour: int = 14,
        horizon: int = 12,
    ) -> List[Dict]:
        """Generate Top-3 station and time-slot recommendations respecting transformer limits."""
        weights = RECOMMENDATION_MODES.get(mode, RECOMMENDATION_MODES["balanced"])
        hz = max(1, min(horizon, 24))

        cluster_pct, station_util, _ = ForecastService.get_cluster_and_station_forecasts()

        candidates = []
        for offset in range(hz):
            h = (start_hour + offset) % 24
            grid_pct = float(cluster_pct[2][h]) * 100.0  # P90 forecast load
            risk = float(np.clip((grid_pct / 100.0 - WARN_THRESHOLD) / (1.0 - WARN_THRESHOLD), 0.0, 1.0))
            mean_u = float(np.mean([station_util[i][2][h] for i in station_util]))

            for station in STATIONS_CONFIG:
                sid = station["id"]
                u = float(station_util[sid][2][h])
                wait = erlang_c_wait_min(station["chargers"], u)
                score = (
                    weights[0] * (wait / 60.0)
                    + weights[1] * (station["detour"] / 15.0)
                    + weights[2] * max(u - mean_u, 0.0)
                    + weights[3] * risk
                    + DELAY_WEIGHT * (offset / hz)
                )

                candidates.append({
                    "station": station["name"],
                    "station_id": sid,
                    "hour": h,
                    "starts_in_h": offset,
                    "wait_min": round(wait, 1),
                    "detour_min": station["detour"],
                    "grid_load_pct": round(grid_pct, 1),
                    "score": round(score, 3),
                })

        # Hard transformer constraint: prefer slots <= 90% limit
        valid_candidates = [c for c in candidates if c["grid_load_pct"] <= CRIT_THRESHOLD * 100.0] or candidates

        # Dedup to top candidate per station, then sort by score
        best_per_station = {}
        for cand in sorted(valid_candidates, key=lambda c: c["score"]):
            best_per_station.setdefault(cand["station_id"], cand)

        return list(best_per_station.values())[:3]
