"""Feature engineering pipeline for EV cluster load forecasting."""
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd


FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "holiday",
    "temperature",
    "rain",
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "rolling_mean_4h",
    "rolling_mean_24h",
    "chargers_available",
    "active_sessions",
]


def build_feature_dataframe(
    load_records: List[Dict],
    weather_records: List[Dict],
    station_configs: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    """
    Construct model-ready feature dataframe from station load and weather records.
    Features:
      - hour: hour of day (0-23)
      - day_of_week: day of week (0-6)
      - holiday: weekend / holiday indicator (0 or 1)
      - temperature: ambient temperature in Celsius
      - rain: precipitation in mm
      - lag_1h, lag_24h, lag_168h: historical active load lags
      - rolling_mean_4h, rolling_mean_24h: rolling window load averages
      - chargers_available: total chargers minus active chargers
      - active_sessions: concurrent active charging sessions
    """
    df_load = pd.DataFrame(load_records)
    df_wx = pd.DataFrame(weather_records)

    if df_load.empty:
        return pd.DataFrame()

    df_load["timestamp"] = pd.to_datetime(df_load["timestamp"])
    df_load = df_load.sort_values(by=["station_id", "timestamp"]).reset_index(drop=True)

    # Merge weather
    if not df_wx.empty:
        df_wx["timestamp"] = pd.to_datetime(df_wx["timestamp"])
        df = pd.merge(df_load, df_wx[["timestamp", "temperature_c", "precipitation_mm"]], on="timestamp", how="left")
        df["temperature"] = df["temperature_c"].ffill().bfill().fillna(25.0)
        df["rain"] = df["precipitation_mm"].ffill().bfill().fillna(0.0)
    else:
        df = df_load.copy()
        df["temperature"] = 25.0
        df["rain"] = 0.0

    # Temporal features
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek
    df["holiday"] = (df["day_of_week"] >= 5).astype(int)

    # Station capacity mapping for chargers available
    station_chargers_map = {
        s["id"]: s.get("chargers", 6) for s in (station_configs or [])
    }
    df["total_chargers"] = df["station_id"].map(lambda sid: station_chargers_map.get(sid, 6))
    df["chargers_available"] = np.maximum(df["total_chargers"] - df["active_chargers"], 0)
    df["active_sessions"] = df["active_chargers"]

    # Compute lags and rolling means grouped by station
    grouped = df.groupby("station_id")

    df["lag_1h"] = grouped["active_kw"].shift(1)
    df["lag_24h"] = grouped["active_kw"].shift(24)
    # If 168h (1 week) lag is unavailable due to series length, fall back to lag 24h
    df["lag_168h"] = grouped["active_kw"].shift(168).fillna(df["lag_24h"])

    df["rolling_mean_4h"] = grouped["active_kw"].transform(lambda x: x.shift(1).rolling(4, min_periods=1).mean())
    df["rolling_mean_24h"] = grouped["active_kw"].transform(lambda x: x.shift(1).rolling(24, min_periods=1).mean())

    # Backfill earliest rows with seasonal median to avoid dropna losing initial days
    for col in ["lag_1h", "lag_24h", "lag_168h", "rolling_mean_4h", "rolling_mean_24h"]:
        df[col] = df[col].bfill().fillna(df["active_kw"])

    return df
