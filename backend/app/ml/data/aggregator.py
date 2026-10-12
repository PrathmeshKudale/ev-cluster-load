"""Hourly station load aggregation and missing hours validation."""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple

import pandas as pd


def aggregate_sessions_to_hourly_load(
    sessions: List[Dict],
    stations: List[Dict],
    start_dt: datetime,
    end_dt: datetime,
) -> Tuple[List[Dict], Dict[str, Dict]]:
    """
    Aggregate charging sessions into an hourly time-grid per station.
    Computes active delivered kW, concurrent active chargers, and utilization rate.
    Identifies and reports missing hours per station.
    
    Returns:
        (station_load_records, missing_hours_report)
    """
    # Ensure start and end are aligned to the top of the hour
    start_hour = start_dt.replace(minute=0, second=0, microsecond=0)
    end_hour = end_dt.replace(minute=0, second=0, microsecond=0)

    # Build full hourly time index
    total_hours = int((end_hour - start_hour).total_seconds() // 3600)
    all_hours = [start_hour + timedelta(hours=i) for i in range(total_hours)]

    station_map = {s["id"]: s for s in stations}
    load_records = []
    missing_report = {}

    for s in stations:
        sid = s["id"]
        chargers_count = s.get("chargers", 1)
        # Support both explicit "capacity_kw" and per-charger "kw" × "chargers" schema
        if "capacity_kw" in s:
            capacity_kw = s["capacity_kw"]
        else:
            capacity_kw = s.get("kw", 7.4) * chargers_count

        # Filter sessions belonging to this station
        s_sessions = [sess for sess in sessions if sess["station_id"] == sid]

        station_records_map = {}
        for h_start in all_hours:
            h_end = h_start + timedelta(hours=1)

            active_kw = 0.0
            active_chargers = 0

            for sess in s_sessions:
                s_start = sess["start_time"]
                s_end = sess.get("end_time") or (s_start + timedelta(hours=2))

                # Check for overlap between [s_start, s_end] and [h_start, h_end]
                overlap_start = max(s_start, h_start)
                overlap_end = min(s_end, h_end)

                if overlap_start < overlap_end:
                    overlap_hours = (overlap_end - overlap_start).total_seconds() / 3600.0
                    duration_total = max((s_end - s_start).total_seconds() / 3600.0, 0.1)
                    # Average power delivered during the session
                    avg_power_kw = sess["energy_kwh"] / duration_total
                    active_kw += avg_power_kw * overlap_hours
                    active_chargers += 1

            active_kw = round(min(active_kw, capacity_kw), 2)
            active_chargers = min(active_chargers, chargers_count)
            util_rate = round(active_kw / max(capacity_kw, 1.0), 3)

            station_records_map[h_start] = {
                "station_id": sid,
                "timestamp": h_start,
                "active_kw": active_kw,
                "active_chargers": active_chargers,
                "utilization_rate": util_rate,
            }

        # Validate completeness against full grid
        present_count = len(station_records_map)
        missing_count = total_hours - present_count
        missing_report[sid] = {
            "station_name": s["name"],
            "expected_hours": total_hours,
            "present_hours": present_count,
            "missing_hours": missing_count,
            "coverage_pct": round((present_count / max(total_hours, 1)) * 100.0, 2),
        }

        load_records.extend(station_records_map.values())

    load_records.sort(key=lambda r: (r["station_id"], r["timestamp"]))
    return load_records, missing_report
