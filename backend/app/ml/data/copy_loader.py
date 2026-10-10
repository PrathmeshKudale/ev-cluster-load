"""PostgreSQL bulk COPY loader for sessions, station_load, and weather records."""
import csv
import io
import logging
import os
from typing import Dict, List

from app.db.connection import engine

logger = logging.getLogger(__name__)


def generate_sessions_csv(sessions: List[Dict]) -> str:
    """Format session records into in-memory CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for s in sessions:
        writer.writerow([
            s["id"],
            s["charger_id"],
            s["station_id"],
            s["user_hash"],
            s["start_time"].isoformat(),
            s["end_time"].isoformat() if s.get("end_time") else "",
            s["energy_kwh"],
            s["peak_kw"],
            "true" if s.get("is_synthetic", False) else "false",
        ])
    return buf.getvalue()


def generate_station_load_csv(records: List[Dict]) -> str:
    """Format hourly station load records into in-memory CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for r in records:
        writer.writerow([
            r["station_id"],
            r["timestamp"].isoformat(),
            r["active_kw"],
            r["active_chargers"],
            r["utilization_rate"],
        ])
    return buf.getvalue()


def generate_weather_csv(weather_records: List[Dict]) -> str:
    """Format weather observation records into in-memory CSV string."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    for w in weather_records:
        writer.writerow([
            w["cluster_id"],
            w["timestamp"].isoformat(),
            w["temperature_c"],
            w["precipitation_mm"],
            w["wind_speed_ms"],
            w["solar_irradiance"],
        ])
    return buf.getvalue()


def bulk_copy_load(
    sessions: List[Dict],
    station_loads: List[Dict],
    weather_records: List[Dict],
) -> Dict[str, int]:
    """
    Execute high-speed bulk ingestion into PostgreSQL using COPY FROM STDIN.
    Falls back to writing processed CSV files to disk if database is offline.
    """
    sessions_csv = generate_sessions_csv(sessions)
    load_csv = generate_station_load_csv(station_loads)
    weather_csv = generate_weather_csv(weather_records)

    counts = {
        "sessions": len(sessions),
        "station_load": len(station_loads),
        "weather": len(weather_records),
    }

    # Attempt PostgreSQL COPY
    try:
        raw_conn = engine.raw_connection()
        cursor = raw_conn.cursor()

        # Delete matching synthetic sessions and reload via COPY in single transaction
        cursor.execute("DELETE FROM clean.sessions WHERE is_synthetic = true;")
        cursor.execute("DELETE FROM clean.station_load;")
        cursor.execute("DELETE FROM clean.weather;")

        # In psycopg3 / psycopg2 cursor.copy is standard
        with cursor.copy(
            "COPY clean.sessions (id, charger_id, station_id, user_hash, start_time, end_time, energy_kwh, peak_kw, is_synthetic) FROM STDIN WITH (FORMAT CSV)"
        ) as copy:
            copy.write(sessions_csv)

        with cursor.copy(
            "COPY clean.station_load (station_id, timestamp, active_kw, active_chargers, utilization_rate) FROM STDIN WITH (FORMAT CSV)"
        ) as copy:
            copy.write(load_csv)

        with cursor.copy(
            "COPY clean.weather (cluster_id, timestamp, temperature_c, precipitation_mm, wind_speed_ms, solar_irradiance) FROM STDIN WITH (FORMAT CSV)"
        ) as copy:
            copy.write(weather_csv)

        raw_conn.commit()
        cursor.close()
        raw_conn.close()
        logger.info("Successfully executed bulk COPY into PostgreSQL database.")
        return counts
    except Exception as exc:
        logger.warning(
            "PostgreSQL bulk COPY skipped (database offline or unreachable: %s). "
            "Writing processed CSV buffers to data/processed/.",
            exc,
        )

    # Offline filesystem fallback
    out_dir = "data/processed"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "sessions.csv"), "w", encoding="utf-8") as f:
        f.write(sessions_csv)
    with open(os.path.join(out_dir, "station_load.csv"), "w", encoding="utf-8") as f:
        f.write(load_csv)
    with open(os.path.join(out_dir, "weather.csv"), "w", encoding="utf-8") as f:
        f.write(weather_csv)
    logger.info("Saved %d sessions, %d station_load, and %d weather rows to %s", counts["sessions"], counts["station_load"], counts["weather"], out_dir)
    return counts
