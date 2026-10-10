"""ACN-Data ingestion adapter with deterministic synthetic fallback and virtual station splitting."""
import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import httpx
import numpy as np

logger = logging.getLogger(__name__)

# Virtual stations partition definition (3-5 stations with different capacities)
VIRTUAL_STATIONS = [
    {
        "id": "VS1",
        "name": "Market Road Hub",
        "chargers": 8,
        "max_kw": 7.4,
        "capacity_kw": 59.2,
        "weight": 0.35,
    },
    {
        "id": "VS2",
        "name": "Station Plaza AC",
        "chargers": 6,
        "max_kw": 7.4,
        "capacity_kw": 44.4,
        "weight": 0.25,
    },
    {
        "id": "VS3",
        "name": "College Gate Fast",
        "chargers": 6,
        "max_kw": 11.0,
        "capacity_kw": 66.0,
        "weight": 0.25,
    },
    {
        "id": "VS4",
        "name": "Ring Road DC Hub",
        "chargers": 4,
        "max_kw": 22.0,
        "capacity_kw": 88.0,
        "weight": 0.15,
    },
]


def hash_user_id(raw_id: str) -> str:
    """Hash raw driver/user identifier using SHA-256 (no PII)."""
    return hashlib.sha256(f"acn_driver_salt_{raw_id}".encode()).hexdigest()


def generate_synthetic_acn_sessions(
    start_dt: datetime,
    days: int = 14,
    seed: int = 42,
) -> List[Dict]:
    """Generate realistic, deterministic EV charging sessions mimicking ACN-Data patterns."""
    rng = np.random.default_rng(seed)
    sessions = []
    session_counter = 1

    for day in range(days):
        current_date = (start_dt + timedelta(days=day)).date()
        is_weekend = (start_dt + timedelta(days=day)).weekday() >= 5
        # Weekday volume is higher in workplace/urban clusters
        daily_sessions_count = int(rng.poisson(lam=36 if not is_weekend else 18))

        for _ in range(daily_sessions_count):
            # Arrival distribution: morning peak around 08:30 (std 1.5) and afternoon around 13:00 (std 2.0)
            if rng.random() < 0.65:
                arrival_hour = float(np.clip(rng.normal(8.5, 1.4), 6.0, 12.0))
            else:
                arrival_hour = float(np.clip(rng.normal(13.2, 2.1), 11.0, 20.0))

            arrival_time = datetime.combine(
                current_date,
                datetime.min.time(),
                tzinfo=timezone.utc,
            ) + timedelta(hours=arrival_hour)

            # Duration distribution: 1 to 6 hours
            duration_hours = float(np.clip(rng.lognormal(mean=0.8, sigma=0.5), 0.5, 8.0))
            departure_time = arrival_time + timedelta(hours=duration_hours)

            # Pick virtual station based on capacity weights
            v_idx = int(rng.choice(len(VIRTUAL_STATIONS), p=[s["weight"] for s in VIRTUAL_STATIONS]))
            station = VIRTUAL_STATIONS[v_idx]
            charger_num = int(rng.integers(1, station["chargers"] + 1))
            charger_id = f"{station['id']}-C{charger_num}"

            # Charging profile: delivered energy
            rated_kw = station["max_kw"]
            active_charge_hours = min(duration_hours, float(rng.uniform(1.2, 3.5)))
            energy_kwh = round(float(np.clip(active_charge_hours * rated_kw * 0.92, 4.0, 75.0)), 2)

            raw_user_num = int(rng.integers(100, 999))
            sessions.append({
                "id": f"acn-synth-{session_counter:05d}",
                "charger_id": charger_id,
                "station_id": station["id"],
                "user_hash": hash_user_id(str(raw_user_num)),
                "start_time": arrival_time,
                "end_time": departure_time,
                "energy_kwh": energy_kwh,
                "peak_kw": rated_kw,
                "is_synthetic": True,
            })
            session_counter += 1

    sessions.sort(key=lambda s: s["start_time"])
    return sessions


def fetch_acn_data(
    start_dt: Optional[datetime] = None,
    days: int = 14,
    site: str = "caltech",
    timeout_sec: float = 3.0,
) -> Tuple[List[Dict], str]:
    """
    Fetch ACN-Data sessions using token from .env; falls back to deterministic generator
    if token is missing, download fails, or network is offline.
    """
    if start_dt is None:
        start_dt = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)

    token = os.getenv("ACN_DATA_API_TOKEN") or os.getenv("ACN_TOKEN")
    if not token:
        logger.warning(
            "ACN-Data API token not set in environment (.env); "
            "falling back to deterministic synthetic generator."
        )
        return generate_synthetic_acn_sessions(start_dt, days=days), "synthetic_fallback"

    end_dt = start_dt + timedelta(days=days)
    url = f"https://ev.caltech.edu/api/v1/sessions/{site}"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "where": f'connectionTime >= "{start_dt.strftime("%a, %d %b %Y 00:00:00 GMT")}" and connectionTime <= "{end_dt.strftime("%a, %d %b %Y 23:59:59 GMT")}"'
    }

    try:
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("_items", [])
                if items:
                    parsed_sessions = []
                    for idx, item in enumerate(items):
                        c_time = datetime.fromisoformat(item["connectionTime"].replace("Z", "+00:00"))
                        d_time = datetime.fromisoformat(item["disconnectTime"].replace("Z", "+00:00")) if item.get("disconnectTime") else c_time + timedelta(hours=2)
                        kwh = float(item.get("kWhDelivered", 12.0))
                        
                        # Map ACN site space to one of the 3-5 virtual stations
                        v_idx = idx % len(VIRTUAL_STATIONS)
                        station = VIRTUAL_STATIONS[v_idx]
                        c_id = f"{station['id']}-C{(idx % station['chargers']) + 1}"

                        parsed_sessions.append({
                            "id": f"acn-live-{item.get('_id', idx)}",
                            "charger_id": c_id,
                            "station_id": station["id"],
                            "user_hash": hash_user_id(str(item.get("userID", f"user_{idx}"))),
                            "start_time": c_time,
                            "end_time": d_time,
                            "energy_kwh": round(kwh, 2),
                            "peak_kw": station["max_kw"],
                            "is_synthetic": True,  # virtual stations mapped from single site
                        })
                    logger.info("Successfully fetched %d live sessions from ACN-Data (%s).", len(parsed_sessions), site)
                    return parsed_sessions, "live_acn"
    except Exception as exc:
        logger.warning(
            "ACN-Data request failed (%s); falling back to deterministic synthetic generator.",
            exc,
        )

    return generate_synthetic_acn_sessions(start_dt, days=days), "synthetic_fallback"
