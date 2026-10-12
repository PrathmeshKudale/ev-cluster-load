"""Dataset builders for temporal sliding windows and multi-station graph tensor batches."""
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

from app.ml.features import FEATURE_COLUMNS, build_feature_dataframe
from app.ml.data.acn_adapter import VIRTUAL_STATIONS, fetch_acn_data
from app.ml.data.urban_ev_adapter import fetch_urbanev_data
from app.ml.data.weather_adapter import fetch_open_meteo_weather
from app.ml.data.aggregator import aggregate_sessions_to_hourly_load
from app.db.seed import DEMO_STATIONS

FEATURE_COLUMNS_NO_WEATHER = [
    col for col in FEATURE_COLUMNS if col not in ("temperature", "rain")
]


class TimeSeriesSequenceDataset(Dataset):
    """
    Sliding window dataset for sequence-to-sequence quantile forecasting.
    Produces (X_window, y_horizon) where:
      - X_window has shape (seq_len, num_features)
      - y_horizon has shape (horizon, )
    """

    def __init__(
        self,
        features: np.ndarray,
        targets: np.ndarray,
        seq_len: int = 48,
        horizon: int = 24,
    ):
        self.seq_len = seq_len
        self.horizon = horizon

        num_samples = len(features) - seq_len - horizon + 1
        if num_samples <= 0:
            raise ValueError(
                f"Series length {len(features)} is too short for seq_len={seq_len} + horizon={horizon}"
            )

        self.X_windows = []
        self.y_targets = []

        for i in range(num_samples):
            self.X_windows.append(features[i : i + seq_len])
            self.y_targets.append(targets[i + seq_len : i + seq_len + horizon])

        self.X_windows = torch.tensor(np.array(self.X_windows), dtype=torch.float32)
        self.y_targets = torch.tensor(np.array(self.y_targets), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.X_windows)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.X_windows[idx], self.y_targets[idx]


class SpatioTemporalGraphDataset(Dataset):
    """
    Multi-station spatio-temporal sliding window dataset for ST-GNN.
    Produces (X_spatial_window, y_station_horizon, y_cluster_horizon) where:
      - X_spatial_window has shape (seq_len, num_stations, num_features)
      - y_station_horizon has shape (num_stations, horizon)
      - y_cluster_horizon has shape (horizon, )
    """

    def __init__(
        self,
        station_features: np.ndarray,  # (T, num_stations, num_features)
        station_targets: np.ndarray,   # (T, num_stations)
        cluster_targets: np.ndarray,   # (T, )
        seq_len: int = 48,
        horizon: int = 24,
    ):
        self.seq_len = seq_len
        self.horizon = horizon

        total_t = len(cluster_targets)
        num_samples = total_t - seq_len - horizon + 1
        if num_samples <= 0:
            raise ValueError(f"Series length {total_t} too short for seq_len={seq_len} + horizon={horizon}")

        self.X_windows = []
        self.y_station_targets = []
        self.y_cluster_targets = []

        for i in range(num_samples):
            self.X_windows.append(station_features[i : i + seq_len])
            # (horizon, num_stations) -> transpose to (num_stations, horizon)
            st_target = station_targets[i + seq_len : i + seq_len + horizon].T
            self.y_station_targets.append(st_target)
            self.y_cluster_targets.append(cluster_targets[i + seq_len : i + seq_len + horizon])

        self.X_windows = torch.tensor(np.array(self.X_windows), dtype=torch.float32)
        self.y_station_targets = torch.tensor(np.array(self.y_station_targets), dtype=torch.float32)
        self.y_cluster_targets = torch.tensor(np.array(self.y_cluster_targets), dtype=torch.float32)

    def __len__(self) -> int:
        return len(self.X_windows)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.X_windows[idx], self.y_station_targets[idx], self.y_cluster_targets[idx]


def prepare_forecasting_data(
    days: int = 21,
    use_weather: bool = True,
) -> Dict:
    """
    Load raw EV sessions, aggregate loads, compute features, and generate time-aligned arrays.
    Returns:
        Dictionary containing train/calib/test dataframes, feature column list,
        station mappings, and raw feature arrays.
    """
    from datetime import datetime, timedelta, timezone

    start_dt = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    acn_sessions, _ = fetch_acn_data(start_dt=start_dt, days=days)
    uev_sessions, _ = fetch_urbanev_data(start_dt=start_dt, days=days)
    all_sessions = acn_sessions + uev_sessions
    end_dt = start_dt + timedelta(days=days)

    loads, _ = aggregate_sessions_to_hourly_load(
        sessions=all_sessions,
        stations=DEMO_STATIONS,
        start_dt=start_dt,
        end_dt=end_dt,
    )
    weather, _ = fetch_open_meteo_weather(start_dt=start_dt, days=days)

    df_features = build_feature_dataframe(loads, weather, DEMO_STATIONS)
    target = "active_kw"

    feature_cols = FEATURE_COLUMNS if use_weather else FEATURE_COLUMNS_NO_WEATHER

    # Standardize features using train split statistics
    timestamps = sorted(df_features["timestamp"].unique())
    n_ts = len(timestamps)
    train_end = timestamps[int(n_ts * 0.60)]
    calib_end = timestamps[int(n_ts * 0.80)]

    df_train = df_features[df_features["timestamp"] < train_end]
    mean_vals = df_train[feature_cols].mean()
    std_vals = df_train[feature_cols].std().replace(0, 1.0)

    # Normalized features
    df_norm = df_features.copy()
    for col in feature_cols:
        df_norm[col] = (df_norm[col] - mean_vals[col]) / std_vals[col]

    # Cluster-aggregated hourly load
    df_cluster = (
        df_features.groupby("timestamp")
        .agg({
            target: "sum",
            **{c: "mean" for c in feature_cols if c != target},
        })
        .reset_index()
    )

    return {
        "df_raw": df_features,
        "df_norm": df_norm,
        "df_cluster": df_cluster,
        "feature_cols": feature_cols,
        "train_end": train_end,
        "calib_end": calib_end,
        "mean_vals": mean_vals,
        "std_vals": std_vals,
        "target_col": target,
        "stations": DEMO_STATIONS,
    }
