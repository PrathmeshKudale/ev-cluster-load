"""Tests for database schemas, models, configuration tables, hypertables, and seed idempotency."""
import pytest
from sqlalchemy import text

from app.db.connection import engine, SessionLocal
from app.db.models import (
    Base,
    RawAcnSession,
    RawWeatherObservation,
    RawStationTelemetry,
    Cluster,
    Transformer,
    Station,
    Charger,
    Session as EvSession,
    StationLoad,
    Weather,
    Forecast,
    TransformerRisk,
    Recommendation,
    SimRun,
    SimMetric,
    User,
    AuditLog,
    ConfigTransformer,
    ConfigDeratingCurve,
    ConfigTodTariff,
    StationEdge,
    HourlyClusterFeature,
)
from app.db.seed import seed_cluster


def is_database_reachable():
    """Check if the configured PostgreSQL database is accessible."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            return True
    except Exception:
        return False


def test_models_metadata_schemas():
    """Verify all 20 tables are registered in the correct architectural schemas."""
    expected_schemas = {
        # Raw
        "raw.acn_sessions": "raw",
        "raw.weather_observations": "raw",
        "raw.station_telemetry": "raw",
        # Clean
        "clean.clusters": "clean",
        "clean.transformers": "clean",
        "clean.stations": "clean",
        "clean.chargers": "clean",
        "clean.sessions": "clean",
        "clean.station_load": "clean",
        "clean.weather": "clean",
        "clean.forecasts": "clean",
        "clean.transformer_risk": "clean",
        "clean.recommendations": "clean",
        "clean.sim_runs": "clean",
        "clean.sim_metrics": "clean",
        "clean.users": "clean",
        "clean.audit_log": "clean",
        "clean.config_transformer": "clean",
        "clean.config_derating_curve": "clean",
        "clean.config_tod_tariff": "clean",
        # Features
        "features.station_edges": "features",
        "features.hourly_cluster_features": "features",
    }

    registered = {f"{table.schema}.{table.name}": table.schema for table in Base.metadata.tables.values()}
    for full_name, schema in expected_schemas.items():
        assert full_name in registered, f"Missing table {full_name} in metadata"
        assert registered[full_name] == schema


@pytest.mark.skipif(not is_database_reachable(), reason="Live PostgreSQL/TimescaleDB database is not reachable")
def test_hypertables_exist_in_timescaledb():
    """Verify that sessions, station_load, weather, and forecasts are created as TimescaleDB hypertables."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT hypertable_schema, hypertable_name FROM timescaledb_information.hypertables;")
        )
        hypertables = {row[1] for row in result.fetchall()}
        required = {"sessions", "station_load", "weather", "forecasts"}
        missing = required - hypertables
        assert not missing, f"Expected hypertables not found in TimescaleDB: {missing}"


@pytest.mark.skipif(not is_database_reachable(), reason="Live PostgreSQL/TimescaleDB database is not reachable")
def test_seed_idempotency_identical_row_counts():
    """Verify running the seed twice yields identical row counts (Acceptance requirement)."""
    with SessionLocal() as db:
        first_counts = seed_cluster(db)
        second_counts = seed_cluster(db)

        assert first_counts == second_counts, (
            f"Seed counts differ between runs:\nRun 1: {first_counts}\nRun 2: {second_counts}"
        )
        assert first_counts["stations"] == 4
        assert first_counts["transformers"] == 1
        assert first_counts["station_edges"] == 12
        assert first_counts["config_derating_curve"] > 0
        assert first_counts["config_tod_tariff"] > 0
