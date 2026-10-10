"""Geospatial routing and ST-GNN graph edge builder with OSRM and Haversine fallback."""
import math
import os
import logging
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# Default urban travel speed for fallback calculation (km/h)
DEFAULT_URBAN_SPEED_KMH = 28.0
# Public OSRM routing endpoint or local environment configuration
OSRM_DEFAULT_URL = os.getenv("OSRM_URL", "http://router.project-osrm.org")


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers."""
    r = 6371.0088  # Earth mean radius in kilometers
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(r * c, 3)


def estimate_drive_minutes(distance_km: float, speed_kmh: float = DEFAULT_URBAN_SPEED_KMH) -> float:
    """Estimate urban driving duration in minutes from road distance."""
    if distance_km <= 0.0:
        return 0.0
    minutes = (distance_km / max(speed_kmh, 1.0)) * 60.0
    return round(max(minutes, 1.0), 2)


def get_driving_route(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    osrm_base_url: Optional[str] = None,
    timeout_sec: float = 1.5,
) -> Tuple[float, float, str]:
    """
    Get driving distance (km) and travel duration (minutes) between two coordinates.
    Attempts OSRM first; if unreachable, times out, or errors, gracefully falls back to Haversine.
    
    Returns:
        (distance_km, drive_minutes, source_method) where source_method is 'osrm' or 'haversine_estimate'.
    """
    base_url = (osrm_base_url or OSRM_DEFAULT_URL).rstrip("/")
    # Coordinates in OSRM are passed as {longitude},{latitude}
    url = f"{base_url}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"

    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    distance_km = round(route["distance"] / 1000.0, 3)
                    drive_minutes = round(route["duration"] / 60.0, 2)
                    return distance_km, max(drive_minutes, 1.0), "osrm"
    except Exception as exc:
        logger.debug("OSRM routing unavailable (%s), using Haversine fallback.", exc)

    # Fallback to spherical geometry
    dist = haversine_distance_km(lat1, lon1, lat2, lon2)
    duration = estimate_drive_minutes(dist)
    return dist, duration, "haversine_estimate"


def build_station_edges(
    stations: List[Dict],
    osrm_base_url: Optional[str] = None,
) -> List[Dict]:
    """
    Construct directed station edges for all station pairs in the cluster graph.
    Computes distance, drive minutes, source method, and normalized adjacency weight.
    """
    edges = []
    for src in stations:
        for dst in stations:
            if src["id"] == dst["id"]:
                continue
            dist_km, drive_min, method = get_driving_route(
                src["latitude"],
                src["longitude"],
                dst["latitude"],
                dst["longitude"],
                osrm_base_url=osrm_base_url,
            )
            # Adjacency weight decays with distance for ST-GNN message passing
            weight = round(1.0 / (1.0 + dist_km), 4)
            edges.append({
                "src_station_id": src["id"],
                "dst_station_id": dst["id"],
                "distance_km": dist_km,
                "drive_minutes": drive_min,
                "source_method": method,
                "weight": weight,
            })
    return edges
