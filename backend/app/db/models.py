"""SQLAlchemy models for EV Cluster Load across raw, clean, and features schemas."""
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    Text,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.connection import Base


def utcnow():
    return datetime.now(timezone.utc)


# ==============================================================================
# RAW SCHEMA: Immutable as ingested
# ==============================================================================

class RawAcnSession(Base):
    """Raw EV charging session ingested directly from ACN-Data / UrbanEV."""
    __tablename__ = "acn_sessions"
    __table_args__ = {"schema": "raw"}

    id = Column(String(64), primary_key=True)
    session_id = Column(String(128), index=True)
    station_id = Column(String(64), index=True)
    user_hash = Column(String(64), index=True)
    connection_time = Column(DateTime(timezone=True))
    disconnect_time = Column(DateTime(timezone=True))
    kwh_delivered = Column(Float)
    raw_payload = Column(Text)
    ingested_at = Column(DateTime(timezone=True), default=utcnow)


class RawWeatherObservation(Base):
    """Raw weather payload ingested directly from Open-Meteo."""
    __tablename__ = "weather_observations"
    __table_args__ = {"schema": "raw"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String(64), index=True)
    observation_time = Column(DateTime(timezone=True), index=True)
    raw_json = Column(Text)
    ingested_at = Column(DateTime(timezone=True), default=utcnow)


class RawStationTelemetry(Base):
    """Raw meter / charger telemetry ingested from OCPP 1.6J MeterValues."""
    __tablename__ = "station_telemetry"
    __table_args__ = {"schema": "raw"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    station_id = Column(String(64), index=True)
    evse_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), index=True)
    meter_value_wh = Column(Float)
    active_kw = Column(Float)
    ingested_at = Column(DateTime(timezone=True), default=utcnow)


# ==============================================================================
# CLEAN SCHEMA: Typed, deduplicated, UTC timestamps, hypertables
# ==============================================================================

class Cluster(Base):
    """Geographic cluster of charging stations under shared grid infrastructure."""
    __tablename__ = "clusters"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    transformers = relationship("Transformer", back_populates="cluster")
    stations = relationship("Station", back_populates="cluster")


class Transformer(Base):
    """Substation transformer supplying power to the cluster."""
    __tablename__ = "transformers"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    cluster_id = Column(String(64), ForeignKey("clean.clusters.id"), nullable=False)
    name = Column(String(128), nullable=False)
    rating_kva = Column(Float, nullable=False, default=100.0)
    power_factor = Column(Float, nullable=False, default=0.95)
    warn_threshold_pct = Column(Float, nullable=False, default=0.80)
    crit_threshold_pct = Column(Float, nullable=False, default=0.90)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    cluster = relationship("Cluster", back_populates="transformers")
    stations = relationship("Station", back_populates="transformer")


class Station(Base):
    """Physical EV charging site with chargers and detour time."""
    __tablename__ = "stations"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    cluster_id = Column(String(64), ForeignKey("clean.clusters.id"), nullable=False)
    transformer_id = Column(String(64), ForeignKey("clean.transformers.id"), nullable=False)
    name = Column(String(128), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    detour_min = Column(Float, nullable=False, default=0.0)
    is_synthetic = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    cluster = relationship("Cluster", back_populates="stations")
    transformer = relationship("Transformer", back_populates="stations")
    chargers = relationship("Charger", back_populates="station")


class Charger(Base):
    """Individual EVSE charger plug at a charging station."""
    __tablename__ = "chargers"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    evse_id = Column(Integer, nullable=False)
    max_kw = Column(Float, nullable=False, default=7.4)
    connector_type = Column(String(64), default="Type 2")
    status = Column(String(32), default="Available")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    station = relationship("Station", back_populates="chargers")


class Session(Base):
    """Charging session records (Timescale hypertable partitioned on start_time)."""
    __tablename__ = "sessions"
    __table_args__ = (
        PrimaryKeyConstraint("id", "start_time"),
        {"schema": "clean"},
    )

    id = Column(String(64), nullable=False)
    charger_id = Column(String(64), ForeignKey("clean.chargers.id"), nullable=False)
    station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    user_hash = Column(String(64), nullable=False, index=True)  # SHA-256 hashed, NO PII
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    energy_kwh = Column(Float)
    peak_kw = Column(Float)
    is_synthetic = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class StationLoad(Base):
    """Hourly aggregated station load (Timescale hypertable partitioned on timestamp)."""
    __tablename__ = "station_load"
    __table_args__ = (
        PrimaryKeyConstraint("station_id", "timestamp"),
        {"schema": "clean"},
    )

    station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    active_kw = Column(Float, nullable=False)
    active_chargers = Column(Integer, nullable=False, default=0)
    utilization_rate = Column(Float, nullable=False, default=0.0)


class Weather(Base):
    """Clean hourly weather observations (Timescale hypertable partitioned on timestamp)."""
    __tablename__ = "weather"
    __table_args__ = (
        PrimaryKeyConstraint("cluster_id", "timestamp"),
        {"schema": "clean"},
    )

    cluster_id = Column(String(64), ForeignKey("clean.clusters.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    temperature_c = Column(Float)
    precipitation_mm = Column(Float)
    wind_speed_ms = Column(Float)
    solar_irradiance = Column(Float)


class Forecast(Base):
    """Calibrated quantile forecasts (Timescale hypertable partitioned on target_ts)."""
    __tablename__ = "forecasts"
    __table_args__ = (
        PrimaryKeyConstraint("station_id", "issued_at", "target_ts"),
        {"schema": "clean"},
    )

    station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False)
    target_ts = Column(DateTime(timezone=True), nullable=False)
    p10 = Column(Float, nullable=False)
    p50 = Column(Float, nullable=False)
    p90 = Column(Float, nullable=False)
    model_version = Column(String(64), nullable=False)


class TransformerRisk(Base):
    """Proactive transformer overload monitoring and alert states."""
    __tablename__ = "transformer_risk"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    transformer_id = Column(String(64), ForeignKey("clean.transformers.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    forecast_p90_pct = Column(Float, nullable=False)
    risk_level = Column(String(32), nullable=False)  # ok / warning / critical
    alert_raised = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class Recommendation(Base):
    """Smart charging Top-3 station and time-slot recommendation log."""
    __tablename__ = "recommendations"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    session_request_id = Column(String(64), index=True)
    user_hash = Column(String(64), index=True)
    mode = Column(String(32), nullable=False)  # fastest / balanced / grid_friendly
    recommended_station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    recommended_slot_start = Column(DateTime(timezone=True), nullable=False)
    rank = Column(Integer, nullable=False)  # 1, 2, 3
    score = Column(Float, nullable=False)
    expected_wait_min = Column(Float)
    expected_detour_min = Column(Float)
    grid_load_pct = Column(Float)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class SimRun(Base):
    """Simulation run tracking for SimPy FCFS vs. Smart Dispatch benchmarks."""
    __tablename__ = "sim_runs"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    dispatch_strategy = Column(String(64), nullable=False)  # fcfs / smart_dispatch
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    config_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class SimMetric(Base):
    """Measured benchmark metrics produced strictly by SimPy simulation runs."""
    __tablename__ = "sim_metrics"
    __table_args__ = {"schema": "clean"}

    id = Column(String(64), primary_key=True)
    sim_run_id = Column(String(64), ForeignKey("clean.sim_runs.id"), nullable=False)
    peak_load_kw = Column(Float)
    peak_shaved_pct = Column(Float)
    overload_warn_hours = Column(Float)
    overload_crit_hours = Column(Float)
    mean_wait_min = Column(Float)
    jain_fairness_index = Column(Float)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class User(Base):
    """Anonymized user table with zero personal identifiable information (PII)."""
    __tablename__ = "users"
    __table_args__ = {"schema": "clean"}

    user_hash = Column(String(64), primary_key=True)  # SHA-256 hash
    preferences_json = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    """System audit trail for configuration changes and dispatch decisions."""
    __tablename__ = "audit_log"
    __table_args__ = {"schema": "clean"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64))
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), default=utcnow)


# ==============================================================================
# CONFIGURATION TABLES (in clean schema): Outside code
# ==============================================================================

class ConfigTransformer(Base):
    """Externalized transformer electrical parameters."""
    __tablename__ = "config_transformer"
    __table_args__ = {"schema": "clean"}

    transformer_id = Column(String(64), ForeignKey("clean.transformers.id"), primary_key=True)
    nominal_kva = Column(Float, nullable=False, default=100.0)
    power_factor = Column(Float, nullable=False, default=0.95)
    warn_threshold_pct = Column(Float, nullable=False, default=0.80)
    crit_threshold_pct = Column(Float, nullable=False, default=0.90)
    cooling_class = Column(String(32), default="ONAN")
    ambient_ref_temp_c = Column(Float, default=30.0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ConfigDeratingCurve(Base):
    """Thermal derating factor vs. ambient temperature for transformer protection."""
    __tablename__ = "config_derating_curve"
    __table_args__ = {"schema": "clean"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    transformer_id = Column(String(64), ForeignKey("clean.transformers.id"), nullable=False)
    ambient_temp_c = Column(Float, nullable=False)
    derating_factor = Column(Float, nullable=False)  # e.g., 1.00 at 30C, 0.85 at 45C
    description = Column(String(128))


class ConfigTodTariff(Base):
    """Indian Time-of-Day (ToD) tariff time slots and energy rates."""
    __tablename__ = "config_tod_tariff"
    __table_args__ = {"schema": "clean"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False)  # Solar Off-Peak, Evening Peak, etc.
    start_hour = Column(Integer, nullable=False)
    end_hour = Column(Integer, nullable=False)
    rate_inr_per_kwh = Column(Float, nullable=False)
    peak_multiplier = Column(Float, nullable=False, default=1.0)
    description = Column(String(128))


# ==============================================================================
# FEATURES SCHEMA: Model-ready representations & graph topology
# ==============================================================================

class StationEdge(Base):
    """Graph edges connecting cluster stations for the Spatio-Temporal GNN (ST-GNN)."""
    __tablename__ = "station_edges"
    __table_args__ = (
        PrimaryKeyConstraint("src_station_id", "dst_station_id"),
        {"schema": "features"},
    )

    src_station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    dst_station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    distance_km = Column(Float, nullable=False)
    drive_minutes = Column(Float, nullable=False)
    source_method = Column(String(32), nullable=False)  # 'osrm' or 'haversine_estimate'
    weight = Column(Float, nullable=False, default=1.0)  # normalized adjacency weight
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class HourlyClusterFeature(Base):
    """Model-ready feature table combining temporal lags, weather, and tariffs."""
    __tablename__ = "hourly_cluster_features"
    __table_args__ = (
        PrimaryKeyConstraint("station_id", "timestamp"),
        {"schema": "features"},
    )

    station_id = Column(String(64), ForeignKey("clean.stations.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    hour_of_day = Column(Integer)
    day_of_week = Column(Integer)
    is_weekend = Column(Boolean)
    active_kw = Column(Float)
    lag_load_1h = Column(Float)
    lag_load_24h = Column(Float)
    temp_c = Column(Float)
    tod_tariff_multiplier = Column(Float)
