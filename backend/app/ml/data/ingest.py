"""Main data ingestion pipeline coordinating ACN-Data, UrbanEV, Open-Meteo, aggregation, and COPY loading."""
import logging
import sys
from datetime import datetime, timezone
from typing import Dict

from app.ml.data.acn_adapter import VIRTUAL_STATIONS, fetch_acn_data
from app.ml.data.urban_ev_adapter import fetch_urbanev_data
from app.ml.data.weather_adapter import fetch_open_meteo_weather
from app.ml.data.aggregator import aggregate_sessions_to_hourly_load
from app.ml.data.copy_loader import bulk_copy_load
from app.ml.data.eda import generate_eda_plots

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("ingest")


def run_ingest(days: int = 14) -> Dict:
    """Run full data ingestion, aggregation, COPY loading, and EDA plot generation."""
    print("=" * 70)
    print("           EV CLUSTER LOAD - DATA INGESTION PIPELINE")
    print("=" * 70)

    start_dt = datetime(2026, 9, 15, 0, 0, tzinfo=timezone.utc)
    from datetime import timedelta
    end_dt = start_dt + timedelta(days=days)

    # 1. Ingest ACN-Data
    print("\n[1/5] Ingesting ACN-Data charging sessions...")
    acn_sessions, acn_mode = fetch_acn_data(start_dt=start_dt, days=days)
    print(f"      - Mode: {acn_mode.upper()}")
    print(f"      - Sessions retrieved: {len(acn_sessions)}")

    # 2. Ingest UrbanEV Data
    print("\n[2/5] Ingesting UrbanEV fast-charging sessions...")
    uev_sessions, uev_mode = fetch_urbanev_data(start_dt=start_dt, days=days)
    print(f"      - Mode: {uev_mode.upper()}")
    print(f"      - Sessions retrieved: {len(uev_sessions)}")

    combined_sessions = acn_sessions + uev_sessions
    print(f"      -> Total combined sessions: {len(combined_sessions)}")

    # 3. Ingest Open-Meteo Weather
    print("\n[3/5] Ingesting Open-Meteo hourly weather observations...")
    weather_records, wx_mode = fetch_open_meteo_weather(start_dt=start_dt, days=days)
    print(f"      - Mode: {wx_mode.upper()}")
    print(f"      - Hourly weather observations: {len(weather_records)}")

    # 4. Hourly Aggregation & Missing Hours Analysis
    print("\n[4/5] Aggregating sessions into hourly station_load grid...")
    station_loads, missing_report = aggregate_sessions_to_hourly_load(
        sessions=combined_sessions,
        stations=VIRTUAL_STATIONS,
        start_dt=start_dt,
        end_dt=end_dt,
    )
    print(f"      -> Total station_load records: {len(station_loads)}")

    print("\n" + "-" * 70)
    print("            MISSING HOURS ANALYSIS PER VIRTUAL STATION")
    print("-" * 70)
    print(f"{'Station':<8} | {'Name':<22} | {'Expected':<8} | {'Present':<8} | {'Missing':<8} | {'Coverage'}")
    print("-" * 70)
    for sid, rep in missing_report.items():
        print(
            f"{sid:<8} | {rep['station_name']:<22} | {rep['expected_hours']:<8} | "
            f"{rep['present_hours']:<8} | {rep['missing_hours']:<8} | {rep['coverage_pct']:.1f}%"
        )
    print("-" * 70)

    # 5. Bulk COPY Loading
    print("\n[5/5] Executing high-speed COPY bulk load...")
    loaded_counts = bulk_copy_load(
        sessions=combined_sessions,
        station_loads=station_loads,
        weather_records=weather_records,
    )
    print(f"      - Sessions loaded:     {loaded_counts['sessions']}")
    print(f"      - Station loads loaded: {loaded_counts['station_load']}")
    print(f"      - Weather rows loaded:  {loaded_counts['weather']}")

    # 6. Generate EDA Plots
    print("\n[6/6] Generating EDA plots in docs/img/...")
    plot_files = generate_eda_plots(
        sessions=combined_sessions,
        station_loads=station_loads,
        weather_records=weather_records,
        output_dir="../docs/img",
    )
    for pf in plot_files:
        print(f"      - Created plot: {pf}")

    print("\n" + "=" * 70)
    print("Ingestion pipeline successfully completed!")
    print("=" * 70 + "\n")

    return {
        "sessions": len(combined_sessions),
        "station_load": len(station_loads),
        "weather": len(weather_records),
        "missing_report": missing_report,
        "plots": plot_files,
    }


if __name__ == "__main__":
    run_ingest()
