"""Deterministic database seeder for EV Cluster Load.

Builds a demo cluster of 4 stations on a 100 kVA transformer, configuration tables,
ST-GNN station edges, and synthetic historical data.
Guarantees identical row counts on repeated executions (idempotent).
"""
import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.connection import SessionLocal, engine
from app.db.models import (
    Cluster,
    Transformer,
    Station,
    Charger,
    Session as EvSession,
    StationLoad,
    Weather,
    ConfigTransformer,
    ConfigDeratingCurve,
    ConfigTodTariff,
    StationEdge,
)
from app.graph.routing import build_station_edges

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Fixed Demo Cluster Configuration
CLUSTER_ID = "C1"
TRANSFORMER_ID = "T1"

DEMO_STATIONS = [
    {
        "id": "S1",
        "name": "Market Road",
        "chargers": 8,
        "kw": 7.4,
        "latitude": 12.9716,
        "longitude": 77.5946,
        "detour": 0.0,
        "pop": 1.25,
    },
    {
        "id": "S2",
        "name": "Station Plaza",
        "chargers": 6,
        "kw": 7.4,
        "latitude": 12.9815,
        "longitude": 77.6083,
        "detour": 4.0,
        "pop": 0.90,
    },
    {
        "id": "S3",
        "name": "College Gate",
        "chargers": 6,
        "kw": 7.4,
        "latitude": 12.9611,
        "longitude": 77.5855,
        "detour": 7.0,
        "pop": 0.60,
    },
    {
        "id": "S4",
        "name": "Ring Road Hub",
        "chargers": 4,
        "kw": 7.4,
        "latitude": 12.9922,
        "longitude": 77.5620,
        "detour": 10.0,
        "pop": 0.50,
    },
]

DERATING_STEPS = [
    (25.0, 1.05, "Cold ambient margin"),
    (30.0, 1.00, "Nominal IEEE/IEC reference rating"),
    (35.0, 0.96, "Mild ambient thermal derating"),
    (40.0, 0.91, "High summer ambient derating"),
    (45.0, 0.85, "Severe summer peak derating"),
    (50.0, 0.77, "Extreme heatwave emergency limit"),
]

TOD_TARIFFS = [
    ("Night Off-Peak", 23, 6, 5.00, 0.85, "Overnight EV grid balancing tariff"),
    ("Morning Normal", 6, 9, 6.50, 1.00, "Standard morning commercial tariff"),
    ("Solar Off-Peak", 9, 17, 5.50, 0.85, "Daytime solar generation soaking tariff"),
    ("Evening Peak", 17, 23, 8.50, 1.25, "Substation evening grid peak surcharge"),
]


def deterministic_user_hash(user_num: int) -> str:
    """Generate deterministic SHA-256 hash for anonymized driver identifier."""
    return hashlib.sha256(f"ev_driver_salt_2026_{user_num}".encode()).hexdigest()


def seed_cluster(db: Session) -> Dict[str, int]:
    """Execute deterministic cluster seeding inside an active session."""
    rng = np.random.default_rng(seed=42)

    # 1. Clean existing records for cluster C1 and transformer T1
    db.execute(text("DELETE FROM clean.clusters WHERE id = :cid"), {"cid": CLUSTER_ID})
    db.execute(text("DELETE FROM clean.config_tod_tariff"))
    db.flush()

    # 2. Insert Cluster
    cluster = Cluster(
        id=CLUSTER_ID,
        name="Metro Central Cluster",
        description="4-station urban cluster fed by a 100 kVA distribution transformer",
    )
    db.add(cluster)

    # 3. Insert Transformer
    transformer = Transformer(
        id=TRANSFORMER_ID,
        cluster_id=CLUSTER_ID,
        name="TX-Metro-100kVA",
        rating_kva=100.0,
        power_factor=0.95,
        warn_threshold_pct=0.80,
        crit_threshold_pct=0.90,
    )
    db.add(transformer)
    db.flush()

    # 4. Insert Configuration Tables
    cfg_tx = ConfigTransformer(
        transformer_id=TRANSFORMER_ID,
        nominal_kva=100.0,
        power_factor=0.95,
        warn_threshold_pct=0.80,
        crit_threshold_pct=0.90,
        cooling_class="ONAN",
        ambient_ref_temp_c=30.0,
    )
    db.add(cfg_tx)

    for temp_c, factor, desc in DERATING_STEPS:
        db.add(ConfigDeratingCurve(
            transformer_id=TRANSFORMER_ID,
            ambient_temp_c=temp_c,
            derating_factor=factor,
            description=desc,
        ))

    for name, sh, eh, rate, mult, desc in TOD_TARIFFS:
        db.add(ConfigTodTariff(
            name=name,
            start_hour=sh,
            end_hour=eh,
            rate_inr_per_kwh=rate,
            peak_multiplier=mult,
            description=desc,
        ))

    # 5. Insert Stations and Chargers
    for s_info in DEMO_STATIONS:
        station = Station(
            id=s_info["id"],
            cluster_id=CLUSTER_ID,
            transformer_id=TRANSFORMER_ID,
            name=s_info["name"],
            latitude=s_info["latitude"],
            longitude=s_info["longitude"],
            detour_min=s_info["detour"],
            is_synthetic=True,
        )
        db.add(station)

        for c_idx in range(1, s_info["chargers"] + 1):
            db.add(Charger(
                id=f"{s_info['id']}-C{c_idx}",
                station_id=s_info["id"],
                evse_id=c_idx,
                max_kw=s_info["kw"],
                connector_type="Type 2",
                status="Available",
            ))
    db.flush()

    # 6. Build ST-GNN Station Edges (features schema)
    # Delete existing edges first
    db.execute(text("DELETE FROM features.station_edges"))
    edges = build_station_edges(DEMO_STATIONS)
    for edge in edges:
        db.add(StationEdge(**edge))

    # 7. Seed Synthetic Historical Sessions & Aggregated Station Load (7 days)
    base_time = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)
    total_hours = 7 * 24

    # Seed hourly weather
    for h in range(total_hours):
        ts = base_time + timedelta(hours=h)
        hour_of_day = ts.hour
        # Diurnal temperature cycle: low ~22C at night, high ~33C in afternoon
        temp = round(22.0 + 11.0 * np.sin(np.pi * (hour_of_day - 8) / 12), 1)
        db.add(Weather(
            cluster_id=CLUSTER_ID,
            timestamp=ts,
            temperature_c=temp,
            precipitation_mm=0.0,
            wind_speed_ms=round(2.5 + rng.uniform(-0.5, 0.5), 1),
            solar_irradiance=round(max(0.0, 800.0 * np.sin(np.pi * (hour_of_day - 6) / 12)), 1),
        ))

    # Hourly aggregated station load
    for s_info in DEMO_STATIONS:
        sid = s_info["id"]
        c_count = s_info["chargers"]
        kw_per_charger = s_info["kw"]
        pop = s_info["pop"]

        for h in range(total_hours):
            ts = base_time + timedelta(hours=h)
            hod = ts.hour
            # Diurnal bell curves peaking at 09:00 and 18:00
            profile = 0.12 + 0.55 * np.exp(-((hod - 18) ** 2) / 8.0) + 0.30 * np.exp(-((hod - 9) ** 2) / 6.0)
            util = float(np.clip(profile * pop * rng.normal(1.0, 0.05), 0.0, 0.95))
            active_chargers = int(round(util * c_count))
            active_kw = round(active_chargers * kw_per_charger, 2)

            db.add(StationLoad(
                station_id=sid,
                timestamp=ts,
                active_kw=active_kw,
                active_chargers=active_chargers,
                utilization_rate=round(util, 3),
            ))

    # Seed individual sessions (120 deterministic charging sessions)
    for s_idx in range(120):
        # Pick station deterministically
        s_choice = DEMO_STATIONS[s_idx % len(DEMO_STATIONS)]
        c_choice = f"{s_choice['id']}-C{(s_idx % s_choice['chargers']) + 1}"
        start_hour_offset = (s_idx * 1.4) % total_hours
        start_ts = base_time + timedelta(hours=start_hour_offset)
        duration_h = 1.0 + (s_idx % 3) * 0.5
        end_ts = start_ts + timedelta(hours=duration_h)
        kwh = round(duration_h * s_choice["kw"] * 0.9, 2)

        db.add(EvSession(
            id=f"sess-202610-d3-{s_idx:04d}",
            charger_id=c_choice,
            station_id=s_choice["id"],
            user_hash=deterministic_user_hash(s_idx),
            start_time=start_ts,
            end_time=end_ts,
            energy_kwh=kwh,
            peak_kw=s_choice["kw"],
            is_synthetic=True,
        ))

    db.commit()

    # Collect row counts for validation
    counts = {
        "clusters": db.query(Cluster).count(),
        "transformers": db.query(Transformer).count(),
        "stations": db.query(Station).count(),
        "chargers": db.query(Charger).count(),
        "config_transformer": db.query(ConfigTransformer).count(),
        "config_derating_curve": db.query(ConfigDeratingCurve).count(),
        "config_tod_tariff": db.query(ConfigTodTariff).count(),
        "station_edges": db.query(StationEdge).count(),
        "weather": db.query(Weather).count(),
        "station_load": db.query(StationLoad).count(),
        "sessions": db.query(EvSession).count(),
    }
    return counts


def run_seed():
    """CLI entrypoint for seeding."""
    logger.info("Connecting to database and running deterministic seed...")
    with SessionLocal() as session:
        counts = seed_cluster(session)
        logger.info("Seed completed successfully! Table row counts:")
        for table, count in counts.items():
            logger.info("  - %s: %d rows", table, count)
        return counts


if __name__ == "__main__":
    run_seed()
