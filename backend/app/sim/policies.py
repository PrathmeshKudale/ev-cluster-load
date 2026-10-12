"""Dispatch policies: FCFS (nearest station) and Smart (recommendation-aware).

Policy interface
----------------
Each policy is a callable:

    station = policy(arrival: dict, stations: list[ChargingStation]) -> ChargingStation

FCFS Policy
-----------
Select the geographically nearest station to the driver's current position,
irrespective of queue length.  Driver location is drawn from a uniform jitter
around the cluster centroid (±0.01° lat/lon) to simulate spatial spread.

Smart Policy
------------
Mimics the project's recommendation service.  Selects the station that minimises:

    score(s) = α·queue_depth(s) + β·distance_km(driver, s) + γ·detour_min(s)

where:
  α = 1.0  (queue pressure weight)
  β = 0.5  (travel distance weight in km)
  γ = 0.05 (detour time weight in minutes)

This is a simplified, zero-latency proxy for the FastAPI /api/recommend endpoint.
The ranking logic mirrors app.services.recommend.score_station().
"""
from __future__ import annotations

import math
from typing import Callable, Dict, List, Optional

import numpy as np

from app.sim.station import ChargingStation


# ---------------------------------------------------------------------------
# Haversine distance (km)
# ---------------------------------------------------------------------------
_R_EARTH_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2.0 * _R_EARTH_KM * math.asin(math.sqrt(a))


# ---------------------------------------------------------------------------
# Driver position sampler
# ---------------------------------------------------------------------------
def _sample_driver_position(stations: List[ChargingStation], rng: np.random.Generator) -> tuple[float, float]:
    """
    Sample a random driver latitude/longitude near the cluster centroid.
    Jitter: ±0.015° (~1.7 km) uniformly.
    """
    centroid_lat = float(np.mean([s.latitude for s in stations]))
    centroid_lon = float(np.mean([s.longitude for s in stations]))
    lat = centroid_lat + rng.uniform(-0.015, 0.015)
    lon = centroid_lon + rng.uniform(-0.015, 0.015)
    return lat, lon


# ---------------------------------------------------------------------------
# FCFS Policy: nearest station by great-circle distance
# ---------------------------------------------------------------------------
def make_fcfs_policy(rng: np.random.Generator) -> Callable:
    """Return a FCFS dispatch policy bound to the given RNG."""

    def fcfs(arrival: Dict, stations: List[ChargingStation]) -> ChargingStation:
        driver_lat, driver_lon = _sample_driver_position(stations, rng)
        best = min(
            stations,
            key=lambda s: _haversine_km(driver_lat, driver_lon, s.latitude, s.longitude),
        )
        return best

    fcfs.__name__ = "fcfs"
    return fcfs


# ---------------------------------------------------------------------------
# Smart Policy: recommendation-service score
# ---------------------------------------------------------------------------
_ALPHA = 1.0    # queue pressure
_BETA = 0.5     # distance (km)
_GAMMA = 0.05   # detour (minutes — stored on station as detour_min attribute)


def make_smart_policy(rng: np.random.Generator) -> Callable:
    """Return a Smart dispatch policy bound to the given RNG."""

    def smart(arrival: Dict, stations: List[ChargingStation]) -> ChargingStation:
        driver_lat, driver_lon = _sample_driver_position(stations, rng)

        def score(s: ChargingStation) -> float:
            dist_km = _haversine_km(driver_lat, driver_lon, s.latitude, s.longitude)
            detour = getattr(s, "detour_min", 0.0)
            # Availability pressure: prefer stations with short queues AND free slots
            queue_pressure = s.queue_depth + max(0, s.active_chargers - s.charger_count + 1)
            return _ALPHA * queue_pressure + _BETA * dist_km + _GAMMA * detour

        return min(stations, key=score)

    smart.__name__ = "smart"
    return smart
