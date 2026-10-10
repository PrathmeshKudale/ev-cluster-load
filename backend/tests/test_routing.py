"""Unit tests for geospatial routing and ST-GNN graph edge construction."""
import math
import pytest

from app.graph.routing import (
    haversine_distance_km,
    estimate_drive_minutes,
    get_driving_route,
    build_station_edges,
)


def test_haversine_distance_zero_for_same_point():
    assert haversine_distance_km(12.9716, 77.5946, 12.9716, 77.5946) == 0.0


def test_haversine_distance_known_distance():
    # Bangalore (12.9716, 77.5946) to Mysore (12.2958, 76.6394) is approx ~127-130 km
    dist = haversine_distance_km(12.9716, 77.5946, 12.2958, 76.6394)
    assert 120.0 < dist < 140.0


def test_estimate_drive_minutes():
    # 28 km at 28 km/h is 60 minutes
    assert estimate_drive_minutes(28.0, speed_kmh=28.0) == 60.0
    # 0 km is 0 min
    assert estimate_drive_minutes(0.0) == 0.0


def test_osrm_fallback_to_haversine():
    # Using an unreachable dummy URL to trigger the fallback logic
    dist, minutes, method = get_driving_route(
        12.9716, 77.5946, 12.9815, 77.6083,
        osrm_base_url="http://127.0.0.1:59999",
        timeout_sec=0.2,
    )
    assert method == "haversine_estimate"
    assert dist > 0.0
    assert minutes > 0.0


def test_build_station_edges_completeness():
    stations = [
        {"id": "S1", "latitude": 12.9716, "longitude": 77.5946},
        {"id": "S2", "latitude": 12.9815, "longitude": 77.6083},
        {"id": "S3", "latitude": 12.9611, "longitude": 77.5855},
        {"id": "S4", "latitude": 12.9922, "longitude": 77.5620},
    ]
    edges = build_station_edges(stations, osrm_base_url="http://127.0.0.1:59999")
    # For 4 stations, directed edges = 4 * 3 = 12
    assert len(edges) == 12

    for edge in edges:
        assert edge["src_station_id"] != edge["dst_station_id"]
        assert edge["distance_km"] > 0
        assert edge["drive_minutes"] > 0
        assert 0 < edge["weight"] <= 1.0
        assert edge["source_method"] in ("osrm", "haversine_estimate")
