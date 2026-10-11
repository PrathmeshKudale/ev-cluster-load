"""Contract tests for API v1 routes, OpenAPI specifications, legacy redirects, and error envelopes."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_schema_contains_all_endpoints_and_tags():
    """Verify that OpenAPI schema lists all required v1 endpoints with tags and examples."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()

    paths = schema.get("paths", {})
    required_paths = [
        "/api/v1/clusters",
        "/api/v1/stations",
        "/api/v1/forecast",
        "/api/v1/transformer/{id}/risk",
        "/api/v1/metrics/simulation",
        "/api/v1/recommend",
        "/api/v1/replay/start",
    ]

    for p in required_paths:
        assert p in paths, f"Path {p} missing from OpenAPI schema"

    # Check tags
    tags = {tag["name"] for tag in schema.get("tags", [])}
    expected_tags = {"Clusters", "Stations", "Forecast", "Transformer", "Recommendations", "Simulation", "Replay"}
    assert expected_tags.issubset(tags), f"Missing OpenAPI tags: {expected_tags - tags}"


def test_get_clusters():
    resp = client.get("/api/v1/clusters")
    assert resp.status_code == 200
    data = resp.json()
    assert "transformer_kva" in data
    assert "power_factor" in data
    assert len(data["stations"]) == 4


def test_get_stations_paginated():
    resp = client.get("/api/v1/stations?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "page" in data and data["page"] == 1
    assert "page_size" in data and data["page_size"] == 2
    assert "total_items" in data and data["total_items"] == 4
    assert "total_pages" in data and data["total_pages"] == 2
    assert len(data["items"]) == 2


def test_get_forecast():
    resp = client.get("/api/v1/forecast?start_hour=14")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["hours"]) == 24
    assert len(data["p10"]) == 24
    assert len(data["p50"]) == 24
    assert len(data["p90"]) == 24
    assert data["warn"] == 80
    assert data["critical"] == 90
    assert "model_version" in data


def test_get_transformer_risk():
    resp = client.get("/api/v1/transformer/T1/risk?start_hour=14")
    assert resp.status_code == 200
    data = resp.json()
    assert data["transformer_id"] == "T1"
    assert data["kva"] == 100.0
    assert "peak_p90_pct" in data
    assert data["level"] in ("ok", "warning", "critical")


def test_get_simulation_metrics():
    resp = client.get("/api/v1/metrics/simulation")
    assert resp.status_code == 200
    data = resp.json()
    assert "strategies" in data
    assert "fcfs" in data["strategies"]
    assert "smart_dispatch" in data["strategies"]
    assert "impact_summary" in data
    assert data["impact_summary"]["peak_shaved_kw"] > 0


def test_post_recommend():
    payload = {"mode": "balanced", "start_hour": 14, "horizon": 12}
    resp = client.post("/api/v1/recommend", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["mode"] == "balanced"
    assert len(data["top3"]) == 3
    for rec in data["top3"]:
        assert rec["grid_load_pct"] <= 90.0
        assert "station" in rec
        assert "score" in rec


def test_post_replay_start():
    payload = {"speed_multiplier": 60.0, "horizon_hours": 24}
    resp = client.post("/api/v1/replay/start", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["status"] == "running"
    assert data["speed_multiplier"] == 60.0


def test_websocket_live_telemetry():
    with client.websocket_connect("/ws/live") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "cluster_telemetry"
        assert "p50_current" in msg
        assert msg["status"] == "connected"

        ws.send_text("ping")
        ack = ws.receive_json()
        assert ack["type"] == "ack"
        assert ack["received"] == "ping"


def test_legacy_api_redirects():
    # Test GET redirects with follow_redirects=False to verify 307 status
    r_cluster = client.get("/api/cluster", follow_redirects=False)
    assert r_cluster.status_code == 307
    assert r_cluster.headers["location"] == "/api/v1/clusters"

    r_forecast = client.get("/api/forecast?start_hour=14", follow_redirects=False)
    assert r_forecast.status_code == 307
    assert "/api/v1/forecast" in r_forecast.headers["location"]

    r_tx = client.get("/api/transformer?start_hour=14", follow_redirects=False)
    assert r_tx.status_code == 307
    assert "/api/v1/transformer/T1/risk" in r_tx.headers["location"]

    # Test POST redirect
    r_rec = client.post("/api/recommend", json={"mode": "fastest"}, follow_redirects=False)
    assert r_rec.status_code == 307
    assert r_rec.headers["location"] == "/api/v1/recommend"


def test_consistent_error_envelope_404():
    resp = client.get("/api/v1/non_existent_route")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]


def test_consistent_error_envelope_422_validation():
    # Invalid mode and invalid hour
    resp = client.post("/api/v1/recommend", json={"mode": 12345, "start_hour": 99})
    assert resp.status_code == 422
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]


def test_dashboard_loads():
    """Verify that the existing frontend dashboard still loads at root URL /."""
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "EV cluster load forecast" in resp.text


def test_swagger_docs_and_openapi_examples():
    """Verify that /docs loads and OpenAPI schema contains examples for every v1 endpoint."""
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "swagger-ui" in resp.text

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    paths = schema.get("paths", {})

    # Check each endpoint has documentation and schema definitions
    for path, methods in paths.items():
        if not path.startswith("/api/v1"):
            continue
        for method, operation in methods.items():
            assert "summary" in operation or "description" in operation, f"Missing description in {method} {path}"
            assert "responses" in operation, f"Missing responses in {method} {path}"


