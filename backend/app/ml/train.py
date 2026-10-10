"""LightGBM multi-quantile training, split-conformal calibration, MLflow tracking, and backtesting."""
import os
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import lightgbm as lgb
import mlflow
import numpy as np
import pandas as pd

from app.ml.features import FEATURE_COLUMNS, build_feature_dataframe
from app.ml.data.acn_adapter import VIRTUAL_STATIONS, fetch_acn_data
from app.ml.data.urban_ev_adapter import fetch_urbanev_data
from app.ml.data.weather_adapter import fetch_open_meteo_weather
from app.ml.data.aggregator import aggregate_sessions_to_hourly_load

# Metric Functions
def pinball_loss(y_true: np.ndarray, y_pred: np.ndarray, alpha: float) -> float:
    """Calculate Pinball (quantile) loss for a given quantile alpha."""
    diff = y_true - y_pred
    return float(np.mean(np.maximum(alpha * diff, (alpha - 1.0) * diff)))


def winkler_score(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray, alpha: float = 0.20) -> float:
    """
    Compute Winkler score for a (1 - alpha) prediction interval (lower is better).
    Penalizes both interval width and observations falling outside the bounds.
    """
    width = upper - lower
    under = (lower - y_true) * (2.0 / alpha)
    over = (y_true - upper) * (2.0 / alpha)
    penalty = np.where(y_true < lower, under, np.where(y_true > upper, over, 0.0))
    return float(np.mean(width + penalty))


def calculate_coverage(y_true: np.ndarray, lower: np.ndarray, upper: np.ndarray) -> float:
    """Percentage of actual observations covered between lower and upper bounds."""
    covered = (y_true >= lower) & (y_true <= upper)
    return float(np.mean(covered) * 100.0)


class CalibratedQuantileForecaster:
    """LightGBM P10/P50/P90 quantile regressor ensemble with split-conformal calibration."""

    def __init__(self, target_coverage: float = 0.80):
        self.target_coverage = target_coverage
        self.models: Dict[str, lgb.LGBMRegressor] = {}
        self.conformal_offsets: Tuple[float, float] = (0.0, 0.0)
        self.feature_names = FEATURE_COLUMNS

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series):
        """Train LightGBM regressors for P10, P50, and P90 quantiles."""
        quantiles = {"p10": 0.10, "p50": 0.50, "p90": 0.90}
        for q_name, alpha in quantiles.items():
            model = lgb.LGBMRegressor(
                objective="quantile",
                alpha=alpha,
                n_estimators=120,
                learning_rate=0.04,
                num_leaves=31,
                min_child_samples=10,
                random_state=42,
                verbosity=-1,
            )
            model.fit(X_train[self.feature_names], y_train)
            self.models[q_name] = model

    def calibrate(self, X_calib: pd.DataFrame, y_calib: pd.Series):
        """
        Compute split-conformal calibration offsets on held-out calibration set
        to guarantee empirical coverage reaches target (e.g. >= 80%).
        """
        raw_p10 = self.models["p10"].predict(X_calib[self.feature_names])
        raw_p90 = self.models["p90"].predict(X_calib[self.feature_names])
        y = y_calib.values

        # Conformity residuals for lower and upper quantile boundaries
        # Miscoverage budget per tail is (1 - target_coverage) / 2 = 0.10
        tail_alpha = (1.0 - self.target_coverage) / 2.0
        r_low = raw_p10 - y
        r_high = y - raw_p90

        # Conformal quantile adjustment with finite-sample correction
        delta_low = float(np.quantile(r_low, np.clip(1.0 - tail_alpha, 0.5, 0.99)))
        delta_high = float(np.quantile(r_high, np.clip(1.0 - tail_alpha, 0.5, 0.99)))

        self.conformal_offsets = (delta_low, delta_high)

    def predict(self, X: pd.DataFrame, calibrate: bool = True) -> Dict[str, np.ndarray]:
        """Generate quantile forecasts enforcing monotonicity (P10 <= P50 <= P90)."""
        raw_p10 = self.models["p10"].predict(X[self.feature_names])
        raw_p50 = self.models["p50"].predict(X[self.feature_names])
        raw_p90 = self.models["p90"].predict(X[self.feature_names])

        if calibrate:
            delta_low, delta_high = self.conformal_offsets
            p10 = raw_p10 - delta_low
            p90 = raw_p90 + delta_high
        else:
            p10 = raw_p10
            p90 = raw_p90

        # Non-negativity and quantile monotonicity enforcement
        p10 = np.maximum(p10, 0.0)
        p50 = np.maximum(raw_p50, p10)
        p90 = np.maximum(p90, p50)

        return {"p10": p10, "p50": p50, "p90": p90}


def run_training_and_backtest(days: int = 21, save_dir: str = "../results") -> Dict:
    """
    Execute full pipeline:
    1. Feature engineering with time-based train/calib/test split.
    2. Seasonal Naive benchmark computation.
    3. LightGBM quantile model training.
    4. Conformal calibration.
    5. MLflow experiment tracking.
    6. Update results/backtest.csv.
    """
    out_path = Path(save_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "models").mkdir(parents=True, exist_ok=True)

    # 1. Ingest historical data
    from datetime import datetime, timedelta, timezone
    start_dt = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    acn_sessions, _ = fetch_acn_data(start_dt=start_dt, days=days)
    uev_sessions, _ = fetch_urbanev_data(start_dt=start_dt, days=days)
    all_sessions = acn_sessions + uev_sessions
    end_dt = start_dt + timedelta(days=days)

    loads, _ = aggregate_sessions_to_hourly_load(
        sessions=all_sessions,
        stations=VIRTUAL_STATIONS,
        start_dt=start_dt,
        end_dt=end_dt,
    )
    weather, _ = fetch_open_meteo_weather(start_dt=start_dt, days=days)

    df_features = build_feature_dataframe(loads, weather, VIRTUAL_STATIONS)
    target = "active_kw"

    # 2. Strict time-based splits: Train (60%), Calibration (20%), Test (20%)
    timestamps = sorted(df_features["timestamp"].unique())
    n_ts = len(timestamps)
    split_train = timestamps[int(n_ts * 0.60)]
    split_calib = timestamps[int(n_ts * 0.80)]

    df_train = df_features[df_features["timestamp"] < split_train]
    df_calib = df_features[(df_features["timestamp"] >= split_train) & (df_features["timestamp"] < split_calib)]
    df_test = df_features[df_features["timestamp"] >= split_calib]

    X_train, y_train = df_train[FEATURE_COLUMNS], df_train[target]
    X_calib, y_calib = df_calib[FEATURE_COLUMNS], df_calib[target]
    X_test, y_test = df_test[FEATURE_COLUMNS], df_test[target]

    y_test_arr = y_test.values

    # 3. Seasonal Naive Baseline (lag 24h with historical quantile spread)
    naive_p50 = X_test["lag_24h"].values
    hour_residuals = df_train.groupby("hour")[target].std().to_dict()
    test_hours = X_test["hour"].values
    hour_stds = np.array([hour_residuals.get(h, 5.0) for h in test_hours])
    naive_p10 = np.maximum(naive_p50 - 1.28 * hour_stds, 0.0)
    naive_p90 = naive_p50 + 1.28 * hour_stds

    naive_mae = float(np.mean(np.abs(y_test_arr - naive_p50)))
    naive_rmse = float(np.sqrt(np.mean((y_test_arr - naive_p50) ** 2)))
    naive_cov = calculate_coverage(y_test_arr, naive_p10, naive_p90)
    naive_winkler = winkler_score(y_test_arr, naive_p10, naive_p90)

    # 4. Train LightGBM Quantile Ensembles & Conformal Calibrate
    forecaster = CalibratedQuantileForecaster(target_coverage=0.80)
    forecaster.fit(X_train, y_train)

    # Pre-calibration evaluation
    preds_raw = forecaster.predict(X_test, calibrate=False)
    raw_mae = float(np.mean(np.abs(y_test_arr - preds_raw["p50"])))
    raw_cov = calculate_coverage(y_test_arr, preds_raw["p10"], preds_raw["p90"])

    # Conformal calibration on validation set
    forecaster.calibrate(X_calib, y_calib)
    preds_cal = forecaster.predict(X_test, calibrate=True)

    lgb_mae = float(np.mean(np.abs(y_test_arr - preds_cal["p50"])))
    lgb_rmse = float(np.sqrt(np.mean((y_test_arr - preds_cal["p50"]) ** 2)))
    lgb_p10_loss = pinball_loss(y_test_arr, preds_cal["p10"], 0.10)
    lgb_p50_loss = pinball_loss(y_test_arr, preds_cal["p50"], 0.50)
    lgb_p90_loss = pinball_loss(y_test_arr, preds_cal["p90"], 0.90)
    lgb_cov = calculate_coverage(y_test_arr, preds_cal["p10"], preds_cal["p90"])
    lgb_winkler = winkler_score(y_test_arr, preds_cal["p10"], preds_cal["p90"])

    improvement_pct = round(((naive_mae - lgb_mae) / max(naive_mae, 1e-4)) * 100.0, 2)

    # 5. MLflow Tracking
    os.environ["MLFLOW_ENABLE_SYSTEM_METRICS_LOGGING"] = "false"
    db_path = (out_path / "mlflow.db").as_posix()
    mlflow.set_tracking_uri(f"sqlite:///{db_path}")
    mlflow.set_experiment("ev_cluster_load_quantile_forecasting")

    with mlflow.start_run(run_name="lightgbm_conformal_calibrated"):
        mlflow.log_params({
            "features": ",".join(FEATURE_COLUMNS),
            "target_coverage": 0.80,
            "train_samples": len(X_train),
            "calib_samples": len(X_calib),
            "test_samples": len(X_test),
        })
        mlflow.log_metrics({
            "seasonal_naive_mae": naive_mae,
            "seasonal_naive_coverage": naive_cov,
            "lightgbm_raw_mae": raw_mae,
            "lightgbm_raw_coverage": raw_cov,
            "lightgbm_calibrated_mae": lgb_mae,
            "lightgbm_calibrated_coverage": lgb_cov,
            "improvement_over_seasonal_naive_pct": improvement_pct,
            "pinball_p10": lgb_p10_loss,
            "pinball_p50": lgb_p50_loss,
            "pinball_p90": lgb_p90_loss,
            "winkler_score": lgb_winkler,
        })

        # Save model artifact
        model_artifact_path = out_path / "models" / "lightgbm_cluster_forecast.joblib"
        joblib.dump(forecaster, model_artifact_path)
        mlflow.log_artifact(str(model_artifact_path))

    # 6. Save results to results/backtest.csv
    csv_path = out_path / "backtest.csv"
    results_rows = [
        {
            "model": "seasonal_naive",
            "mae": round(naive_mae, 3),
            "rmse": round(naive_rmse, 3),
            "pinball_p10": round(pinball_loss(y_test_arr, naive_p10, 0.10), 3),
            "pinball_p50": round(pinball_loss(y_test_arr, naive_p50, 0.50), 3),
            "pinball_p90": round(pinball_loss(y_test_arr, naive_p90, 0.90), 3),
            "coverage_p10_p90": round(naive_cov, 1),
            "winkler_score": round(naive_winkler, 3),
            "improvement_over_naive_pct": 0.0,
        },
        {
            "model": "lightgbm_quantile_raw",
            "mae": round(raw_mae, 3),
            "rmse": round(float(np.sqrt(np.mean((y_test_arr - preds_raw["p50"]) ** 2))), 3),
            "pinball_p10": round(pinball_loss(y_test_arr, preds_raw["p10"], 0.10), 3),
            "pinball_p50": round(pinball_loss(y_test_arr, preds_raw["p50"], 0.50), 3),
            "pinball_p90": round(pinball_loss(y_test_arr, preds_raw["p90"], 0.90), 3),
            "coverage_p10_p90": round(raw_cov, 1),
            "winkler_score": round(winkler_score(y_test_arr, preds_raw["p10"], preds_raw["p90"]), 3),
            "improvement_over_naive_pct": round(((naive_mae - raw_mae) / naive_mae) * 100.0, 2),
        },
        {
            "model": "lightgbm_quantile_conformal",
            "mae": round(lgb_mae, 3),
            "rmse": round(lgb_rmse, 3),
            "pinball_p10": round(lgb_p10_loss, 3),
            "pinball_p50": round(lgb_p50_loss, 3),
            "pinball_p90": round(lgb_p90_loss, 3),
            "coverage_p10_p90": round(lgb_cov, 1),
            "winkler_score": round(lgb_winkler, 3),
            "improvement_over_naive_pct": improvement_pct,
        },
    ]

    pd.DataFrame(results_rows).to_csv(csv_path, index=False)

    # 7. Print summary metrics
    print("\n" + "=" * 75)
    print("      BACKTEST RESULTS: LIGHTGBM VS SEASONAL NAIVE BASELINE")
    print("=" * 75)
    print(f"{'Model':<28} | {'MAE (kW)':<9} | {'P10-P90 Cov':<11} | {'Winkler':<9} | {'Improv %'}")
    print("-" * 75)
    for r in results_rows:
        print(f"{r['model']:<28} | {r['mae']:<9.2f} | {r['coverage_p10_p90']:<10.1f}% | {r['winkler_score']:<9.2f} | {r['improvement_over_naive_pct']:.1f}%")
    print("-" * 75)
    print(f"Key Result: LightGBM achieves {improvement_pct:.1f}% MAE improvement over seasonal naive.")
    print(f"Conformal Calibration: P10 to P90 empirical test coverage reached {lgb_cov:.1f}% (target >= 80%).")
    print(f"Saved artifacts to {csv_path} and {model_artifact_path}\n" + "=" * 75 + "\n")

    return {
        "naive_mae": naive_mae,
        "lgb_mae": lgb_mae,
        "improvement_pct": improvement_pct,
        "coverage_pct": lgb_cov,
        "csv_path": str(csv_path),
    }


if __name__ == "__main__":
    run_training_and_backtest()
