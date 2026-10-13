"""Inference forecast module providing calibrated LightGBM predictions with Seasonal Naive fallback."""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

try:
    from app.ml.train import CalibratedQuantileForecaster
    if "__main__" in sys.modules and not hasattr(sys.modules["__main__"], "CalibratedQuantileForecaster"):
        setattr(sys.modules["__main__"], "CalibratedQuantileForecaster", CalibratedQuantileForecaster)
except Exception:
    pass

logger = logging.getLogger(__name__)

# Search paths for saved model artifact
MODEL_CANDIDATE_PATHS = [
    Path(__file__).resolve().parents[3] / "results" / "models" / "lightgbm_cluster_forecast.joblib",
    Path(__file__).resolve().parents[2] / "results" / "models" / "lightgbm_cluster_forecast.joblib",
    Path("results/models/lightgbm_cluster_forecast.joblib"),
    Path("../results/models/lightgbm_cluster_forecast.joblib"),
]


def seasonal_naive_fallback(
    stations: List[Dict],
    transformer_kva: float = 100.0,
    power_factor: float = 0.95,
    days: int = 21,
    seed: int = 7,
) -> Tuple[np.ndarray, Dict[str, np.ndarray], str]:
    """Seasonal naive / historical diurnal profile fallback returning identical (3, 24) shapes."""
    rng = np.random.default_rng(seed)
    h = np.arange(24)

    def _profile(hour):
        return 0.12 + 0.55 * np.exp(-((hour - 18) ** 2) / 8.0) + 0.30 * np.exp(-((hour - 9) ** 2) / 6.0)

    history = {
        s["id"]: np.clip(
            np.clip(_profile(h) * s.get("pop", 1.0), 0.0, 1.0) * rng.normal(1.0, 0.18, (days, 24)),
            0.0,
            1.0,
        )
        for s in stations
    }

    def _bands(arr):
        return np.percentile(arr, [10, 50, 90], axis=0)

    cap = {s["id"]: s["chargers"] * s["kw"] for s in stations}
    cluster_load_kw = sum(history[i] * cap[i] for i in cap)
    cluster_pct = _bands(cluster_load_kw / power_factor / transformer_kva)
    station_util = {i: _bands(history[i]) for i in history}

    return cluster_pct, station_util, "seasonal_naive_fallback"


def compute_forecasts(
    stations: List[Dict],
    transformer_kva: float = 100.0,
    power_factor: float = 0.95,
) -> Tuple[np.ndarray, Dict[str, np.ndarray], str]:
    """
    Generate 24-hour calibrated P10, P50, and P90 forecast bands.
    Loads trained CalibratedQuantileForecaster; falls back to seasonal naive if unavailable.
    
    Returns:
        (cluster_pct, station_util, model_version)
        - cluster_pct: np.ndarray of shape (3, 24) where [0]=P10, [1]=P50, [2]=P90
        - station_util: dict mapping station_id to np.ndarray of shape (3, 24)
        - model_version: str identifier of active forecaster
    """
    model_path = None
    for p in MODEL_CANDIDATE_PATHS:
        if p.exists():
            model_path = p
            break

    if not model_path:
        logger.info("Trained LightGBM model artifact not found; using Seasonal Naive fallback.")
        return seasonal_naive_fallback(stations, transformer_kva, power_factor)

    try:
        import app.ml.train as train_mod
        if "__main__" in sys.modules:
            setattr(sys.modules["__main__"], "CalibratedQuantileForecaster", train_mod.CalibratedQuantileForecaster)
        forecaster = joblib.load(model_path)
        cap = {s["id"]: s["chargers"] * s["kw"] for s in stations}
        total_cluster_cap = sum(cap.values())

        station_util = {}
        cluster_p10_kw = np.zeros(24)
        cluster_p50_kw = np.zeros(24)
        cluster_p90_kw = np.zeros(24)

        for s in stations:
            sid = s["id"]
            station_cap = cap[sid]
            chargers_count = s["chargers"]

            # Construct 24 hours of feature vectors for inference
            hours = np.arange(24)
            # Diurnal temperature cycle for Bangalore
            temp = 22.0 + 10.0 * np.sin(np.pi * (hours - 8) / 12.0)
            
            # Synthetic lag representations matching station baseline
            base_kw = station_cap * (0.15 + 0.50 * np.exp(-((hours - 18) ** 2) / 8.0) + 0.25 * np.exp(-((hours - 9) ** 2) / 6.0))
            
            features_df = pd.DataFrame({
                "hour": hours,
                "day_of_week": 2,  # Wednesday representative weekday
                "holiday": 0,
                "temperature": temp,
                "rain": 0.0,
                "lag_1h": np.roll(base_kw, 1),
                "lag_24h": base_kw,
                "lag_168h": base_kw,
                "rolling_mean_4h": pd.Series(base_kw).rolling(4, min_periods=1).mean().values,
                "rolling_mean_24h": np.full(24, np.mean(base_kw)),
                "chargers_available": np.maximum(chargers_count - np.round(base_kw / s["kw"]), 0),
                "active_sessions": np.round(base_kw / s["kw"]),
            })

            preds = forecaster.predict(features_df, calibrate=True)
            s_p10 = np.clip(preds["p10"] / station_cap, 0.0, 1.0)
            s_p50 = np.clip(preds["p50"] / station_cap, 0.0, 1.0)
            s_p90 = np.clip(preds["p90"] / station_cap, 0.0, 1.0)

            # Ensure order
            s_p10 = np.minimum(s_p10, s_p50)
            s_p90 = np.maximum(s_p90, s_p50)

            station_util[sid] = np.array([s_p10, s_p50, s_p90])

            cluster_p10_kw += preds["p10"]
            cluster_p50_kw += preds["p50"]
            cluster_p90_kw += preds["p90"]

        # Cluster load as share of transformer rating (joint kVA)
        denom = power_factor * transformer_kva
        c_p10 = cluster_p10_kw / denom
        c_p50 = cluster_p50_kw / denom
        c_p90 = cluster_p90_kw / denom

        c_p10 = np.minimum(c_p10, c_p50)
        c_p90 = np.maximum(c_p90, c_p50)

        cluster_pct = np.array([c_p10, c_p50, c_p90])
        return cluster_pct, station_util, "lightgbm_quantile_conformal_v1"

    except Exception as exc:
        logger.warning("Error running LightGBM forecast (%s); using Seasonal Naive fallback.", exc)
        return seasonal_naive_fallback(stations, transformer_kva, power_factor)
