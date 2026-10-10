"""Open-Meteo weather adapter with zero API key requirement and offline fallback."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# Bangalore cluster coordinates
CLUSTER_LAT = 12.9716
CLUSTER_LON = 77.5946
CLUSTER_ID = "C1"


def generate_synthetic_weather(
    start_dt: datetime,
    days: int = 14,
    seed: int = 77,
) -> List[Dict]:
    """Generate realistic diurnal weather series matching tropical urban patterns."""
    rng = np.random.default_rng(seed)
    records = []
    total_hours = days * 24

    for h in range(total_hours):
        ts = start_dt + timedelta(hours=h)
        hour_of_day = ts.hour
        # Diurnal temperature cycle: ~21C min to ~32C max
        base_temp = 21.5 + 10.5 * np.sin(np.pi * (hour_of_day - 8) / 12.0)
        temp_c = round(float(np.clip(base_temp + rng.normal(0, 0.4), 14.0, 42.0)), 1)

        # Afternoon brief showers on ~20% of days
        precip = 0.0
        if 15 <= hour_of_day <= 17 and rng.random() < 0.20:
            precip = round(float(rng.uniform(1.0, 8.5)), 1)

        wind = round(float(np.clip(rng.normal(3.2, 0.8), 0.5, 9.0)), 1)
        solar = 0.0
        if 6 <= hour_of_day <= 18:
            solar = round(float(np.clip(850.0 * np.sin(np.pi * (hour_of_day - 6) / 12.0) * (0.8 if precip > 0 else 1.0), 0.0, 950.0)), 1)

        records.append({
            "cluster_id": CLUSTER_ID,
            "timestamp": ts,
            "temperature_c": temp_c,
            "precipitation_mm": precip,
            "wind_speed_ms": wind,
            "solar_irradiance": solar,
        })
    return records


def fetch_open_meteo_weather(
    start_dt: Optional[datetime] = None,
    days: int = 14,
    timeout_sec: float = 3.0,
) -> Tuple[List[Dict], str]:
    """Fetch hourly weather from Open-Meteo free API without keys; falls back to diurnal model offline."""
    if start_dt is None:
        start_dt = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=days)

    start_date_str = start_dt.strftime("%Y-%m-%d")
    end_date_str = end_dt.strftime("%Y-%m-%d")

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": CLUSTER_LAT,
        "longitude": CLUSTER_LON,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,direct_normal_irradiance",
        "timezone": "UTC",
    }

    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                hourly = data.get("hourly", {})
                times = hourly.get("time", [])
                temps = hourly.get("temperature_2m", [])
                precips = hourly.get("precipitation", [])
                winds = hourly.get("wind_speed_10m", [])
                solars = hourly.get("direct_normal_irradiance", [])

                records = []
                for i in range(len(times)):
                    ts = datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc)
                    records.append({
                        "cluster_id": CLUSTER_ID,
                        "timestamp": ts,
                        "temperature_c": float(temps[i]) if temps[i] is not None else 25.0,
                        "precipitation_mm": float(precips[i]) if precips[i] is not None else 0.0,
                        "wind_speed_ms": float(winds[i]) if winds[i] is not None else 2.5,
                        "solar_irradiance": float(solars[i]) if solars[i] is not None else 0.0,
                    })
                logger.info("Successfully fetched %d hourly records from Open-Meteo.", len(records))
                return records, "live_open_meteo"
    except Exception as exc:
        logger.warning(
            "Open-Meteo API unreachable (%s); using deterministic diurnal weather generator.",
            exc,
        )

    return generate_synthetic_weather(start_dt, days=days), "synthetic_fallback"
