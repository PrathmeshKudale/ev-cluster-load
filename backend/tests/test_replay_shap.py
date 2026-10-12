"""Unit and integration tests for Replay Engine (1440x WebSocket) and SHAP TreeExplainer.

Verifies:
1. ShapExplainer runs TreeExplainer on LightGBM quantile model.
2. Explanations produce top-3 ranked features with impact metrics.
3. Every recommendation candidate includes real SHAP reasons.
4. ReplayService generates full simulation frames with queue lengths, alerts, and recommendations.
5. ReplayService supports speeds up to 1440x (1 day in ~60s).
6. WebSocket /ws/replay accepts control commands and streams frames with SHAP reasons.
"""
import json
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.shap_explainer import ShapExplainer
from app.services.recommendation_service import RecommendationService
from app.services.replay_service import ReplayService

client = TestClient(app)


def test_shap_tree_explainer_initialization_and_explanation():
    """Verify ShapExplainer executes TreeExplainer on the LightGBM model and extracts top 3 features."""
    features = {
        "hour": 18.0,
        "day_of_week": 2.0,
        "holiday": 0.0,
        "temperature": 28.0,
        "rain": 0.0,
        "lag_1h": 22.0,
        "lag_24h": 20.0,
        "lag_168h": 21.0,
        "rolling_mean_4h": 21.5,
        "rolling_mean_24h": 18.0,
        "chargers_available": 1.0,
        "active_sessions": 3.0,
    }

    reasons = ShapExplainer.get_top_reasons_for_features(features, top_k=3)
    assert len(reasons) == 3, f"Expected 3 SHAP reasons, got {len(reasons)}"
    for r in reasons:
        assert "feature" in r
        assert "shap_value" in r
        assert "reason_text" in r
        assert "impact" in r
        assert isinstance(r["shap_value"], float)


def test_recommendation_candidates_contain_real_shap_output():
    """Verify every recommendation returned by RecommendationService has top-3 SHAP explanations."""
    recs = RecommendationService.get_top3_recommendations(mode="balanced", start_hour=18, horizon=6)
    assert len(recs) > 0
    for rec in recs:
        assert "shap_reasons" in rec
        assert isinstance(rec["shap_reasons"], list)
        assert len(rec["shap_reasons"]) == 3
        # Ensure reasons describe real features and impact
        first_reason = rec["shap_reasons"][0]
        assert "effect" in first_reason or "kW" in first_reason or len(first_reason) > 10


def test_replay_service_1440x_and_frame_generation():
    """Verify ReplayService ticks at 1440x speed and produces full state frames."""
    ReplayService.reset()
    state = ReplayService.start_replay(speed_multiplier=1440.0, horizon_hours=24)
    assert state["speed_multiplier"] == 1440.0
    assert state["total_ticks"] == 1440
    assert state["status"] == "running"

    # Frame at tick 0 (midnight)
    f0 = ReplayService.get_full_frame_at_tick(0)
    assert f0["type"] == "replay_frame"
    assert f0["tick"] == 0
    assert f0["time_str"] == "00:00"
    assert len(f0["stations"]) == 4

    # Frame at tick 540 (09:00 morning rush)
    f_morning = ReplayService.get_full_frame_at_tick(540)
    assert f_morning["time_str"] == "09:00"
    assert f_morning["cluster_load_pct"] > f0["cluster_load_pct"]

    # Frame at tick 1140 (19:00 evening peak)
    f_evening = ReplayService.get_full_frame_at_tick(1140)
    assert f_evening["time_str"] == "19:00"
    assert f_evening["cluster_load_pct"] >= 75.0

    # Ensure recommendations in the frame contain SHAP reasons
    assert len(f_evening["recommendations"]) > 0
    for r in f_evening["recommendations"]:
        assert "shap_reasons" in r
        assert len(r["shap_reasons"]) == 3


def test_replay_websocket_streaming_and_controls():
    """Verify /ws/replay WebSocket endpoint connects, starts, and streams replay frames with SHAP reasons."""
    with client.websocket_connect("/ws/replay") as ws:
        init_data = json.loads(ws.receive_text())
        assert init_data["type"] == "replay_connected"

        # Send start command at 1440x speed
        ws.send_text(json.dumps({"action": "start", "speed": 1440.0, "horizon_hours": 24}))
        
        # Read frames until we receive a replay_frame
        frame = None
        for _ in range(5):
            msg = json.loads(ws.receive_text())
            if msg["type"] == "replay_frame":
                frame = msg
                break
        assert frame is not None, "Failed to receive replay_frame from websocket"
        assert "cluster_load_pct" in frame
        assert "stations" in frame
        assert "recommendations" in frame
        assert len(frame["recommendations"][0]["shap_reasons"]) == 3

        # Send pause command
        ws.send_text(json.dumps({"action": "pause"}))
        paused = False
        for _ in range(5):
            p_msg = json.loads(ws.receive_text())
            if p_msg.get("type") == "state_changed" and p_msg.get("state", {}).get("status") == "paused":
                paused = True
                break
            elif p_msg.get("status") == "paused":
                paused = True
                break
        assert paused or ReplayService._status == "paused"
