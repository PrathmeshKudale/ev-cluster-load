"""Unit and integration tests for data ingestion, aggregation, COPY formatting, and EDA."""
import os
from datetime import datetime, timedelta, timezone
import pytest

from app.ml.data.acn_adapter import (
    VIRTUAL_STATIONS,
    generate_synthetic_acn_sessions,
    fetch_acn_data,
)
from app.ml.data.urban_ev_adapter import (
    generate_synthetic_urbanev_sessions,
    fetch_urbanev_data,
)
from app.ml.data.weather_adapter import (
    generate_synthetic_weather,
    fetch_open_meteo_weather,
)
from app.ml.data.aggregator import aggregate_sessions_to_hourly_load
from app.ml.data.copy_loader import (
    generate_sessions_csv,
    generate_station_load_csv,
    generate_weather_csv,
    bulk_copy_load,
)
from app.ml.data.eda import generate_eda_plots


def test_virtual_stations_capacities_and_synthetic_flag():
    assert len(VIRTUAL_STATIONS) >= 3 and len(VIRTUAL_STATIONS) <= 5
    station_ids = {s["id"] for s in VIRTUAL_STATIONS}
    assert len(station_ids) == len(VIRTUAL_STATIONS)
    for s in VIRTUAL_STATIONS:
        assert s["capacity_kw"] > 0
        assert s["chargers"] > 0
        assert s["max_kw"] > 0


def test_acn_synthetic_fallback_and_anonymization():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    sessions, mode = fetch_acn_data(start_dt=start, days=3)

    assert len(sessions) > 0
    station_ids = {s["station_id"] for s in sessions}
    assert station_ids.issubset({s["id"] for s in VIRTUAL_STATIONS})

    for s in sessions:
        assert s["is_synthetic"] is True
        assert len(s["user_hash"]) == 64  # SHA-256
        assert s["energy_kwh"] > 0
        assert s["start_time"] < s["end_time"]


def test_urbanev_adapter_fallback():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    sessions, mode = fetch_urbanev_data(start_dt=start, days=3)

    assert len(sessions) > 0
    for s in sessions:
        assert s["is_synthetic"] is True
        assert len(s["user_hash"]) == 64
        assert s["peak_kw"] > 0


def test_weather_hourly_continuity():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    weather = generate_synthetic_weather(start, days=3)

    # 3 days = 72 hours
    assert len(weather) == 72
    for i, w in enumerate(weather):
        assert w["timestamp"] == start + timedelta(hours=i)
        assert 5.0 <= w["temperature_c"] <= 45.0
        assert 0.0 <= w["solar_irradiance"] <= 1200.0


def test_hourly_load_aggregation_and_missing_hours():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=2)  # 48 hours

    dummy_sessions = [
        {
            "id": "s1",
            "station_id": "VS1",
            "charger_id": "VS1-C1",
            "user_hash": "hash1",
            "start_time": start + timedelta(hours=1, minutes=10),
            "end_time": start + timedelta(hours=3, minutes=10),
            "energy_kwh": 14.8,
            "peak_kw": 7.4,
            "is_synthetic": True,
        }
    ]

    loads, report = aggregate_sessions_to_hourly_load(
        sessions=dummy_sessions,
        stations=VIRTUAL_STATIONS,
        start_dt=start,
        end_dt=end,
    )

    # Total load rows = 4 stations * 48 hours = 192 rows
    assert len(loads) == len(VIRTUAL_STATIONS) * 48
    for sid, rep in report.items():
        assert rep["expected_hours"] == 48
        assert rep["present_hours"] == 48
        assert rep["missing_hours"] == 0
        assert rep["coverage_pct"] == 100.0


def test_copy_csv_formatting():
    start = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    sessions = [{
        "id": "s1", "charger_id": "c1", "station_id": "VS1",
        "user_hash": "a" * 64, "start_time": start, "end_time": start + timedelta(hours=1),
        "energy_kwh": 10.0, "peak_kw": 7.4, "is_synthetic": True,
    }]
    csv_text = generate_sessions_csv(sessions)
    assert "VS1" in csv_text
    assert "true" in csv_text


def test_eda_plot_generation(tmp_path):
    start = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    sessions, _ = fetch_acn_data(start_dt=start, days=2)
    loads, _ = aggregate_sessions_to_hourly_load(sessions, VIRTUAL_STATIONS, start, start + timedelta(days=2))
    weather = generate_synthetic_weather(start, days=2)

    plot_dir = tmp_path / "eda_test"
    plots = generate_eda_plots(sessions, loads, weather, output_dir=str(plot_dir))

    assert len(plots) == 3
    for p in plots:
        assert os.path.exists(p)
        assert os.path.getsize(p) > 1000  # valid image file with bytes
