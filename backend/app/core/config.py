"""Application configuration and default cluster constants."""
import os
from typing import Dict, List

TRANSFORMER_KVA: float = 100.0
POWER_FACTOR: float = 0.95
WARN_THRESHOLD: float = 0.80
CRIT_THRESHOLD: float = 0.90
SESSION_HOURS: float = 1.0  # Mean charging session in hours
DELAY_WEIGHT: float = 0.20

# Multi-objective recommendation weights: (wait, detour, imbalance, overload risk)
RECOMMENDATION_MODES: Dict[str, tuple] = {
    "fastest": (0.60, 0.15, 0.10, 0.15),
    "balanced": (0.35, 0.20, 0.25, 0.20),
    "grid_friendly": (0.20, 0.15, 0.30, 0.35),
}

STATIONS_CONFIG: List[Dict] = [
    {"id": "S1", "name": "Market Road", "chargers": 8, "kw": 7.4, "pop": 1.25, "detour": 0, "latitude": 12.9716, "longitude": 77.5946},
    {"id": "S2", "name": "Station Plaza", "chargers": 6, "kw": 7.4, "pop": 0.90, "detour": 4, "latitude": 12.9815, "longitude": 77.6083},
    {"id": "S3", "name": "College Gate", "chargers": 6, "kw": 7.4, "pop": 0.60, "detour": 7, "latitude": 12.9611, "longitude": 77.5855},
    {"id": "S4", "name": "Ring Road Hub", "chargers": 4, "kw": 7.4, "pop": 0.50, "detour": 10, "latitude": 12.9922, "longitude": 77.5620},
]
