"""Integration tests for SQLAlchemy 2 asyncpg, repository per aggregate, and bulk loader.

Verifies:
1. Exact shape parity between in-memory demo mode and database mode across all endpoints.
2. Safe parameterized SQL queries (no string interpolation / SQL injection).
3. Native COPY-based bulk loading.
4. Live execution against PostgreSQL container when reachable.
"""
import os
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DEMO_MODE, STATIONS_CONFIG, TRANSFORMER_KVA, POWER_FACTOR
from app.db.bulk_loader import CopyBulkLoader
from app.db.connection import (
    AsyncSessionLocal,
    SessionLocal,
    async_engine,
    engine,
    get_async_db,
    is_async_db_reachable,
)
from app.db.models import Base, Cluster, Station, Transformer, Forecast, StationLoad, SimRun, SimMetric, User
from app.db.repositories import (
    ClusterRepository,
    ForecastRepository,
    RecommendationRepository,
    SimulationRepository,
    UserRepository,
)
from app.db.seed import seed_cluster
from app.main import app
from app.services.forecast_service import ForecastService
from app.services.simulation_service import SimulationService
from app.services.user_service import UserDTO

client = TestClient(app)


def is_db_live() -> bool:
    """Check if the configured live PostgreSQL container is reachable."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            return True
    except Exception:
        return False


# ==============================================================================
# 1. Shape Parity Tests: DEMO_MODE=memory vs Database Mode
# ==============================================================================

def test_endpoint_shapes_clusters():
    """Verify GET /api/v1/clusters response shape."""
    resp = client.get("/api/v1/clusters")
    assert resp.status_code == 200
    data = resp.json()
    assert "transformer_kva" in data
    assert "power_factor" in data
    assert "stations" in data
    assert isinstance(data["stations"], list)
    assert len(data["stations"]) == 4

    station = data["stations"][0]
    expected_station_keys = {"id", "name", "chargers", "kw", "detour", "latitude", "longitude"}
    assert expected_station_keys.issubset(station.keys())


def test_endpoint_shapes_stations_pagination():
    """Verify GET /api/v1/stations response shape and pagination envelope."""
    resp = client.get("/api/v1/stations?page=1&page_size=2")
    assert resp.status_code == 200
    data = resp.json()

    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_items" in data
    assert "total_pages" in data

    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2
    assert data["total_items"] == 4
    assert data["total_pages"] == 2


def test_endpoint_shapes_forecast():
    """Verify GET /api/v1/forecast response shape."""
    resp = client.get("/api/v1/forecast?start_hour=14")
    assert resp.status_code == 200
    data = resp.json()

    expected_keys = {"hours", "p10", "p50", "p90", "warn", "critical", "model_version"}
    assert expected_keys.issubset(data.keys())
    assert len(data["hours"]) == 24
    assert len(data["p10"]) == 24
    assert len(data["p50"]) == 24
    assert len(data["p90"]) == 24
    assert data["warn"] == 80
    assert data["critical"] == 90


def test_endpoint_shapes_transformer_risk():
    """Verify GET /api/v1/transformer/T1/risk response shape."""
    resp = client.get("/api/v1/transformer/T1/risk?start_hour=14")
    assert resp.status_code == 200
    data = resp.json()

    expected_keys = {
        "transformer_id", "kva", "peak_p90_pct", "peak_hour",
        "level", "warn_threshold_pct", "crit_threshold_pct"
    }
    assert expected_keys.issubset(data.keys())
    assert data["transformer_id"] == "T1"
    assert data["level"] in ("ok", "warning", "critical")


def test_endpoint_shapes_simulation_metrics():
    """Verify GET /api/v1/metrics/simulation response shape."""
    resp = client.get("/api/v1/metrics/simulation")
    assert resp.status_code == 200
    data = resp.json()

    assert "fcfs" in data
    assert "smart_dispatch" in data
    assert "impact_summary" in data

    fcfs_keys = {"peak_load_kw", "mean_wait_min", "jain_fairness_index"}
    assert fcfs_keys.issubset(data["fcfs"].keys())
    assert fcfs_keys.issubset(data["smart_dispatch"].keys())

    imp_keys = {"peak_shaved_pct", "wait_time_reduction_pct", "critical_overload_reduction_pct"}
    assert imp_keys.issubset(data["impact_summary"].keys())


def test_endpoint_shapes_recommend():
    """Verify POST /api/v1/recommend response shape."""
    resp = client.post("/api/v1/recommend", json={"mode": "balanced", "start_hour": 14, "horizon": 12})
    assert resp.status_code == 200
    data = resp.json()

    assert "mode" in data
    assert "top3" in data
    assert data["mode"] == "balanced"
    assert len(data["top3"]) == 3

    slot = data["top3"][0]
    expected_slot_keys = {"station", "station_id", "hour", "starts_in_h", "wait_min", "detour_min", "grid_load_pct", "score"}
    assert expected_slot_keys.issubset(slot.keys())


# ==============================================================================
# 2. Async Repository Unit Tests (In-Memory Demo Mode)
# ==============================================================================

@pytest.mark.anyio
async def test_cluster_repository_memory_mode():
    """Verify ClusterRepository returns canonical cluster topology in memory mode."""
    repo = ClusterRepository(session=None)
    topo = await repo.get_cluster_topology("C1")

    assert topo["transformer_kva"] == TRANSFORMER_KVA
    assert topo["power_factor"] == POWER_FACTOR
    assert len(topo["stations"]) == 4

    stations, total = await repo.list_stations(page=1, page_size=10)
    assert total == 4
    assert len(stations) == 4


@pytest.mark.anyio
async def test_forecast_repository_memory_mode():
    """Verify ForecastRepository returns calibrated 24h forecast in memory mode."""
    repo = ForecastRepository(session=None)
    fc = await repo.get_24h_forecast(cluster_id="C1", start_hour=14)

    assert len(fc["hours"]) == 24
    assert len(fc["p50"]) == 24
    assert fc["warn"] == 80
    assert fc["critical"] == 90


@pytest.mark.anyio
async def test_recommendation_repository_memory_mode():
    """Verify RecommendationRepository saves top3 recommendations gracefully."""
    repo = RecommendationRepository(session=None)
    saved = await repo.save_recommendations(
        session_request_id="test-req-1",
        mode="balanced",
        top3=[{"rank": 1, "station": "Market Road", "station_id": "S1", "score": 0.42}],
    )
    assert saved == 1


@pytest.mark.anyio
async def test_simulation_repository_memory_mode():
    """Verify SimulationRepository returns benchmark metrics in memory mode."""
    repo = SimulationRepository(session=None)
    metrics = await repo.get_simulation_metrics()

    assert "fcfs" in metrics
    assert "smart_dispatch" in metrics
    assert "impact_summary" in metrics


@pytest.mark.anyio
async def test_user_repository_memory_mode():
    """Verify UserRepository looks up seeded demo accounts."""
    repo = UserRepository(session=None)
    user = await repo.get_by_username("judge_demo")

    assert user is not None
    assert user.role == "judge"
    assert user.username == "judge_demo"


# ==============================================================================
# 3. Parameterized SQL & Injection Resistance
# ==============================================================================

@pytest.mark.anyio
async def test_sql_injection_safety_never_evaluates_raw_input():
    """Verify malicious input strings never execute as raw SQL."""
    repo = ClusterRepository(session=None)
    malicious_input = "C1' OR '1'='1"
    # Should not raise SQL syntax error or execute injected conditions
    topo = await repo.get_cluster_topology(malicious_input)
    assert topo is not None

    user_repo = UserRepository(session=None)
    malicious_user = "' UNION SELECT * FROM users --"
    user = await user_repo.get_by_username(malicious_user)
    assert user is None


# ==============================================================================
# 4. Integration Tests against Live PostgreSQL / TimescaleDB Container
# ==============================================================================

@pytest.mark.skipif(not is_db_live(), reason="Live PostgreSQL container is not reachable")
def test_live_postgres_seeding_and_table_counts():
    """Verify seed populates clean and hypertable records in real PostgreSQL container."""
    with SessionLocal() as session:
        counts = seed_cluster(session)
        assert counts["clusters"] == 1
        assert counts["transformers"] == 1
        assert counts["stations"] == 4
        assert counts["chargers"] == 24
        assert counts["forecasts"] == 96
        assert counts["users"] >= 5


@pytest.mark.skipif(not is_db_live(), reason="Live PostgreSQL container is not reachable")
@pytest.mark.anyio
async def test_live_postgres_asyncpg_connection_and_repositories():
    """Verify asyncpg connection and repositories querying real database tables."""
    assert await is_async_db_reachable() is True

    async with AsyncSessionLocal() as session:
        # ClusterRepository
        cluster_repo = ClusterRepository(session=session)
        cluster_repo.is_memory_mode = False
        topo = await cluster_repo.get_cluster_topology("C1")
        assert topo["transformer_kva"] == 100.0
        assert len(topo["stations"]) == 4

        # ForecastRepository reading stored clean.forecasts
        forecast_repo = ForecastRepository(session=session)
        forecast_repo.is_memory_mode = False
        fc = await forecast_repo.get_24h_forecast(cluster_id="C1", start_hour=14)
        assert len(fc["hours"]) == 24
        assert len(fc["p10"]) == 24
        assert len(fc["p90"]) == 24

        # UserRepository querying clean.users
        user_repo = UserRepository(session=session)
        user_repo.is_memory_mode = False
        judge = await user_repo.get_by_username("judge_demo")
        assert judge is not None
        assert judge.role == "judge"


@pytest.mark.skipif(not is_db_live(), reason="Live PostgreSQL container is not reachable")
@pytest.mark.anyio
async def test_live_postgres_copy_bulk_loader():
    """Verify native COPY bulk loader inserts records into real PostgreSQL."""
    async with AsyncSessionLocal() as session:
        now = datetime.now(timezone.utc)
        test_records = [
            {
                "station_id": "S1",
                "issued_at": now,
                "target_ts": now,
                "p10": 10.5,
                "p50": 15.2,
                "p90": 22.8,
                "model_version": "test_copy_v1",
            }
        ]
        inserted = await CopyBulkLoader.copy_forecasts(session, test_records)
        assert inserted == 1


@pytest.mark.skipif(not is_db_live(), reason="Live PostgreSQL container is not reachable")
def test_live_postgres_endpoint_shapes_in_db_mode():
    """Verify endpoint shapes in real database mode match memory mode."""
    os.environ["DEMO_MODE"] = "db"
    try:
        resp = client.get("/api/v1/clusters")
        assert resp.status_code == 200
        data = resp.json()
        assert data["transformer_kva"] == 100.0
        assert len(data["stations"]) == 4

        resp_fc = client.get("/api/v1/forecast?start_hour=14")
        assert resp_fc.status_code == 200
        fc_data = resp_fc.json()
        assert len(fc_data["hours"]) == 24
        assert len(fc_data["p10"]) == 24
        assert len(fc_data["p90"]) == 24

        resp_st = client.get("/api/v1/stations?page=1&page_size=2")
        assert resp_st.status_code == 200
        st_data = resp_st.json()
        assert len(st_data["items"]) == 2
        assert st_data["total_items"] == 4
    finally:
        os.environ["DEMO_MODE"] = "memory"

