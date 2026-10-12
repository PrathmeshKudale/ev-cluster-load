"""Arrival process builder: resamples inter-arrival times and session properties from session data.

Builds empirical bootstrap distributions from real or synthetic session records.
Each seed produces a fresh resampled arrival stream — no two seeds share the same sequence.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import numpy as np


def extract_arrival_distributions(sessions: List[Dict]) -> Dict:
    """
    Extract empirical distributions from a list of session dicts.

    Returns dict with arrays for:
      - inter_arrival_min: minutes between consecutive arrivals (sorted by start_time)
      - duration_min: session durations in minutes
      - energy_kwh: energy delivered per session
      - hour_of_day: float arrival hour (used for weighting station choice in smart policy)
      - station_ids: session station_id list (used to infer empirical station demand mix)
    """
    if not sessions:
        raise ValueError("No sessions provided to extract_arrival_distributions()")

    sorted_sessions = sorted(sessions, key=lambda s: s["start_time"])

    inter_arrivals: List[float] = []
    durations: List[float] = []
    energies: List[float] = []
    hours: List[float] = []
    station_ids: List[str] = []

    prev_time: datetime | None = None
    for sess in sorted_sessions:
        start = sess["start_time"]
        end = sess.get("end_time") or (start + timedelta(hours=2.0))

        dur_min = max((end - start).total_seconds() / 60.0, 5.0)
        kwh = max(float(sess.get("energy_kwh", 1.0)), 0.1)
        hour = start.hour + start.minute / 60.0

        if prev_time is not None:
            gap = (start - prev_time).total_seconds() / 60.0
            if gap > 0:
                inter_arrivals.append(gap)
        prev_time = start

        durations.append(dur_min)
        energies.append(kwh)
        hours.append(hour)
        station_ids.append(str(sess.get("station_id", "S1")))

    return {
        "inter_arrival_min": np.array(inter_arrivals, dtype=np.float64),
        "duration_min": np.array(durations, dtype=np.float64),
        "energy_kwh": np.array(energies, dtype=np.float64),
        "hour_of_day": np.array(hours, dtype=np.float64),
        "station_ids": station_ids,
        "n_sessions": len(sorted_sessions),
    }


def build_arrival_stream(
    dist: Dict,
    sim_duration_min: float,
    rng: np.random.Generator,
) -> List[Dict]:
    """
    Bootstrap-resample session records to fill a simulation window.

    Returns a list of arrival dicts sorted by arrival_min (minutes from sim start):
      {arrival_min, duration_min, energy_kwh, hour_of_day}
    """
    inter_arr = dist["inter_arrival_min"]
    durations = dist["duration_min"]
    energies = dist["energy_kwh"]
    hours = dist["hour_of_day"]

    arrivals: List[Dict] = []
    t = rng.choice(inter_arr)  # random first arrival

    while t < sim_duration_min:
        # Resample a session property vector (joint bootstrap to preserve correlations)
        idx = int(rng.integers(0, len(durations)))
        arrivals.append({
            "arrival_min": float(t),
            "duration_min": float(durations[idx]),
            "energy_kwh": float(energies[idx]),
            "hour_of_day": float(hours[idx]),
        })
        gap = float(rng.choice(inter_arr))
        t += gap

    return arrivals
