"""Tests for LightGBM quantile forecasting, conformal calibration, and backtest results."""
import os
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from app.main import STATIONS, TRANSFORMER_KVA, PF
from app.ml.forecast import compute_forecasts, seasonal_naive_fallback


def test_forecast_module_output_shape_and_types():
    """Verify that compute_forecasts returns the expected (3, 24) shape and ordering."""
    cluster_pct, station_util, version = compute_forecasts(STATIONS, TRANSFORMER_KVA, PF)

    # 1. Cluster percentage shape
    assert isinstance(cluster_pct, np.ndarray)
    assert cluster_pct.shape == (3, 24)

    p10, p50, p90 = cluster_pct[0], cluster_pct[1], cluster_pct[2]
    # Quantiles must be ordered
    assert (p10 <= p50 + 1e-6).all(), "P10 must be <= P50"
    assert (p50 <= p90 + 1e-6).all(), "P50 must be <= P90"
    assert (p10 >= 0.0).all(), "Load percentages must be non-negative"

    # 2. Station utilization shape
    assert isinstance(station_util, dict)
    for s in STATIONS:
        sid = s["id"]
        assert sid in station_util
        s_arr = station_util[sid]
        assert s_arr.shape == (3, 24)
        assert (s_arr[0] <= s_arr[1] + 1e-6).all()
        assert (s_arr[1] <= s_arr[2] + 1e-6).all()


def test_seasonal_naive_fallback_shape_and_order():
    """Verify that the seasonal naive fallback returns identical shape and valid quantiles."""
    cluster_pct, station_util, version = seasonal_naive_fallback(STATIONS, TRANSFORMER_KVA, PF)

    assert cluster_pct.shape == (3, 24)
    p10, p50, p90 = cluster_pct
    assert (p10 <= p50).all() and (p50 <= p90).all()
    assert version == "seasonal_naive_fallback"


def test_backtest_results_csv_exists_and_valid():
    """Verify that results/backtest.csv contains LightGBM rows with measured improvement."""
    candidate_paths = [
        Path("../results/backtest.csv"),
        Path("results/backtest.csv"),
        Path(__file__).resolve().parents[2] / "results" / "backtest.csv",
    ]
    csv_file = next((p for p in candidate_paths if p.exists()), None)
    assert csv_file is not None, "results/backtest.csv not found"

    df = pd.read_csv(csv_file)
    models = set(df["model"].unique())
    assert "seasonal_naive" in models
    assert "lightgbm_quantile_conformal" in models

    lgb_row = df[df["model"] == "lightgbm_quantile_conformal"].iloc[0]
    naive_row = df[df["model"] == "seasonal_naive"].iloc[0]

    assert lgb_row["mae"] < naive_row["mae"]
    assert lgb_row["improvement_over_naive_pct"] > 0.0
    assert lgb_row["coverage_p10_p90"] >= 80.0
