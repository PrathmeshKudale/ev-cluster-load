from fastapi.testclient import TestClient

from app.main import CLUSTER_PCT, app, erlang_c_wait_min

client = TestClient(app)


def test_wait_grows_with_utilisation():
    assert erlang_c_wait_min(6, 0.5) < erlang_c_wait_min(6, 0.8) < erlang_c_wait_min(6, 0.9)


def test_quantiles_are_ordered():
    p10, p50, p90 = CLUSTER_PCT
    assert (p10 <= p50).all() and (p50 <= p90).all()


def test_evening_peak_is_flagged():
    assert client.get("/api/transformer").json()["level"] in ("warning", "critical")


def test_recommend_respects_transformer_limit():
    top = client.post("/api/recommend", json={"mode": "grid_friendly"}).json()["top3"]
    assert len(top) == 3 and all(c["grid_load_pct"] <= 90 for c in top)
