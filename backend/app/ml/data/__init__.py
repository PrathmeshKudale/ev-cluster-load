"""Data ingestion adapters, aggregators, and loaders."""
from app.ml.data.acn_adapter import VIRTUAL_STATIONS, fetch_acn_data
from app.ml.data.urban_ev_adapter import fetch_urbanev_data
from app.ml.data.weather_adapter import fetch_open_meteo_weather
from app.ml.data.aggregator import aggregate_sessions_to_hourly_load
from app.ml.data.copy_loader import bulk_copy_load
from app.ml.data.eda import generate_eda_plots

__all__ = [
    "VIRTUAL_STATIONS",
    "fetch_acn_data",
    "fetch_urbanev_data",
    "fetch_open_meteo_weather",
    "aggregate_sessions_to_hourly_load",
    "bulk_copy_load",
    "generate_eda_plots",
]
