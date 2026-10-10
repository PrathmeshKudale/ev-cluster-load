"""Initial schema creating raw, clean, and features schemas with Timescale hypertables.

Revision ID: 0001
Revises: 
Create Date: 2026-10-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable required PostgreSQL extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis CASCADE;")

    # 2. Create the three architectural schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS raw;")
    op.execute("CREATE SCHEMA IF NOT EXISTS clean;")
    op.execute("CREATE SCHEMA IF NOT EXISTS features;")

    # =========================================================================
    # RAW SCHEMA: Immutable ingested data
    # =========================================================================
    op.create_table(
        "acn_sessions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("session_id", sa.String(128), index=True),
        sa.Column("station_id", sa.String(64), index=True),
        sa.Column("user_hash", sa.String(64), index=True),
        sa.Column("connection_time", sa.DateTime(timezone=True)),
        sa.Column("disconnect_time", sa.DateTime(timezone=True)),
        sa.Column("kwh_delivered", sa.Float()),
        sa.Column("raw_payload", sa.Text()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="raw",
    )

    op.create_table(
        "weather_observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cluster_id", sa.String(64), index=True),
        sa.Column("observation_time", sa.DateTime(timezone=True), index=True),
        sa.Column("raw_json", sa.Text()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="raw",
    )

    op.create_table(
        "station_telemetry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("station_id", sa.String(64), index=True),
        sa.Column("evse_id", sa.Integer()),
        sa.Column("timestamp", sa.DateTime(timezone=True), index=True),
        sa.Column("meter_value_wh", sa.Float()),
        sa.Column("active_kw", sa.Float()),
        sa.Column("ingested_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="raw",
    )

    # =========================================================================
    # CLEAN SCHEMA: Typed, deduplicated, UTC timestamps, hypertables
    # =========================================================================
    op.create_table(
        "clusters",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "transformers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("cluster_id", sa.String(64), sa.ForeignKey("clean.clusters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("rating_kva", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("power_factor", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("warn_threshold_pct", sa.Float(), nullable=False, server_default="0.80"),
        sa.Column("crit_threshold_pct", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "stations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("cluster_id", sa.String(64), sa.ForeignKey("clean.clusters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transformer_id", sa.String(64), sa.ForeignKey("clean.transformers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("detour_min", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )
    # Add PostGIS geometry column for stations
    op.execute("SELECT AddGeometryColumn('clean', 'stations', 'geom', 4326, 'POINT', 2);")
    op.execute("CREATE INDEX idx_stations_geom ON clean.stations USING GIST (geom);")

    op.create_table(
        "chargers",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evse_id", sa.Integer(), nullable=False),
        sa.Column("max_kw", sa.Float(), nullable=False, server_default="7.4"),
        sa.Column("connector_type", sa.String(64), server_default="Type 2"),
        sa.Column("status", sa.String(32), server_default="Available"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(64), nullable=False),
        sa.Column("charger_id", sa.String(64), sa.ForeignKey("clean.chargers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_hash", sa.String(64), nullable=False, index=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True)),
        sa.Column("energy_kwh", sa.Float()),
        sa.Column("peak_kw", sa.Float()),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", "start_time"),
        schema="clean",
    )

    op.create_table(
        "station_load",
        sa.Column("station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active_kw", sa.Float(), nullable=False),
        sa.Column("active_chargers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("utilization_rate", sa.Float(), nullable=False, server_default="0.0"),
        sa.PrimaryKeyConstraint("station_id", "timestamp"),
        schema="clean",
    )

    op.create_table(
        "weather",
        sa.Column("cluster_id", sa.String(64), sa.ForeignKey("clean.clusters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("temperature_c", sa.Float()),
        sa.Column("precipitation_mm", sa.Float()),
        sa.Column("wind_speed_ms", sa.Float()),
        sa.Column("solar_irradiance", sa.Float()),
        sa.PrimaryKeyConstraint("cluster_id", "timestamp"),
        schema="clean",
    )

    op.create_table(
        "forecasts",
        sa.Column("station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("target_ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("p10", sa.Float(), nullable=False),
        sa.Column("p50", sa.Float(), nullable=False),
        sa.Column("p90", sa.Float(), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.PrimaryKeyConstraint("station_id", "issued_at", "target_ts"),
        schema="clean",
    )

    op.create_table(
        "transformer_risk",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("transformer_id", sa.String(64), sa.ForeignKey("clean.transformers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("forecast_p90_pct", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(32), nullable=False),
        sa.Column("alert_raised", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("session_request_id", sa.String(64), index=True),
        sa.Column("user_hash", sa.String(64), index=True),
        sa.Column("mode", sa.String(32), nullable=False),
        sa.Column("recommended_station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommended_slot_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("expected_wait_min", sa.Float()),
        sa.Column("expected_detour_min", sa.Float()),
        sa.Column("grid_load_pct", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "sim_runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("dispatch_strategy", sa.String(64), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("config_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "sim_metrics",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("sim_run_id", sa.String(64), sa.ForeignKey("clean.sim_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("peak_load_kw", sa.Float()),
        sa.Column("peak_shaved_pct", sa.Float()),
        sa.Column("overload_warn_hours", sa.Float()),
        sa.Column("overload_crit_hours", sa.Float()),
        sa.Column("mean_wait_min", sa.Float()),
        sa.Column("jain_fairness_index", sa.Float()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "users",
        sa.Column("user_hash", sa.String(64), primary_key=True),
        sa.Column("preferences_json", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("action", sa.String(64), nullable=False),
        sa.Column("entity_type", sa.String(64), nullable=False),
        sa.Column("entity_id", sa.String(64)),
        sa.Column("details", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    # -------------------------------------------------------------------------
    # Configuration Tables (externalized parameters)
    # -------------------------------------------------------------------------
    op.create_table(
        "config_transformer",
        sa.Column("transformer_id", sa.String(64), sa.ForeignKey("clean.transformers.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nominal_kva", sa.Float(), nullable=False, server_default="100.0"),
        sa.Column("power_factor", sa.Float(), nullable=False, server_default="0.95"),
        sa.Column("warn_threshold_pct", sa.Float(), nullable=False, server_default="0.80"),
        sa.Column("crit_threshold_pct", sa.Float(), nullable=False, server_default="0.90"),
        sa.Column("cooling_class", sa.String(32), server_default="ONAN"),
        sa.Column("ambient_ref_temp_c", sa.Float(), server_default="30.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        schema="clean",
    )

    op.create_table(
        "config_derating_curve",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("transformer_id", sa.String(64), sa.ForeignKey("clean.transformers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ambient_temp_c", sa.Float(), nullable=False),
        sa.Column("derating_factor", sa.Float(), nullable=False),
        sa.Column("description", sa.String(128)),
        schema="clean",
    )

    op.create_table(
        "config_tod_tariff",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("start_hour", sa.Integer(), nullable=False),
        sa.Column("end_hour", sa.Integer(), nullable=False),
        sa.Column("rate_inr_per_kwh", sa.Float(), nullable=False),
        sa.Column("peak_multiplier", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("description", sa.String(128)),
        schema="clean",
    )

    # =========================================================================
    # FEATURES SCHEMA: Model-ready representations & graph topology
    # =========================================================================
    op.create_table(
        "station_edges",
        sa.Column("src_station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dst_station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("drive_minutes", sa.Float(), nullable=False),
        sa.Column("source_method", sa.String(32), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("src_station_id", "dst_station_id"),
        schema="features",
    )

    op.create_table(
        "hourly_cluster_features",
        sa.Column("station_id", sa.String(64), sa.ForeignKey("clean.stations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hour_of_day", sa.Integer()),
        sa.Column("day_of_week", sa.Integer()),
        sa.Column("is_weekend", sa.Boolean()),
        sa.Column("active_kw", sa.Float()),
        sa.Column("lag_load_1h", sa.Float()),
        sa.Column("lag_load_24h", sa.Float()),
        sa.Column("temp_c", sa.Float()),
        sa.Column("tod_tariff_multiplier", sa.Float()),
        sa.PrimaryKeyConstraint("station_id", "timestamp"),
        schema="features",
    )

    # =========================================================================
    # TIMESCALEDB HYPERTABLES: Convert time-series tables
    # =========================================================================
    op.execute("SELECT create_hypertable('clean.sessions', 'start_time', if_not_exists => TRUE);")
    op.execute("SELECT create_hypertable('clean.station_load', 'timestamp', if_not_exists => TRUE);")
    op.execute("SELECT create_hypertable('clean.weather', 'timestamp', if_not_exists => TRUE);")
    op.execute("SELECT create_hypertable('clean.forecasts', 'target_ts', if_not_exists => TRUE);")


def downgrade() -> None:
    op.drop_table("hourly_cluster_features", schema="features")
    op.drop_table("station_edges", schema="features")

    op.drop_table("config_tod_tariff", schema="clean")
    op.drop_table("config_derating_curve", schema="clean")
    op.drop_table("config_transformer", schema="clean")

    op.drop_table("audit_log", schema="clean")
    op.drop_table("users", schema="clean")
    op.drop_table("sim_metrics", schema="clean")
    op.drop_table("sim_runs", schema="clean")
    op.drop_table("recommendations", schema="clean")
    op.drop_table("transformer_risk", schema="clean")
    op.drop_table("forecasts", schema="clean")
    op.drop_table("weather", schema="clean")
    op.drop_table("station_load", schema="clean")
    op.drop_table("sessions", schema="clean")
    op.drop_table("chargers", schema="clean")
    op.drop_table("stations", schema="clean")
    op.drop_table("transformers", schema="clean")
    op.drop_table("clusters", schema="clean")

    op.drop_table("station_telemetry", schema="raw")
    op.drop_table("weather_observations", schema="raw")
    op.drop_table("acn_sessions", schema="raw")

    op.execute("DROP SCHEMA IF EXISTS features CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS clean CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS raw CASCADE;")
