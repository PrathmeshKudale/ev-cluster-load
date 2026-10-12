"""Simulation study runner: executes N seeds × 2 policies and aggregates results.

Entry point:  run_simulation_study()
Output:
  results/sim_summary.json   — mean + 95% CI per metric, labelled as [DES]
  results/sim_*.png          — 6 charts

Session data is loaded from:
  - ACN adapter (real or synthetic fallback)
  - UrbanEV adapter (real or synthetic fallback)

Stations are taken from DEMO_STATIONS (app.db.seed).
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import t as t_dist

from app.db.seed import DEMO_STATIONS
from app.ml.data.acn_adapter import fetch_acn_data
from app.ml.data.urban_ev_adapter import fetch_urbanev_data
from app.sim.arrivals import build_arrival_stream, extract_arrival_distributions
from app.sim.engine import SimResult, run_one_seed
from app.sim.policies import make_fcfs_policy, make_smart_policy

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TRANSFORMER_KVA_LIMIT: float = 100.0   # TX-100kVA cluster feeder
SIM_DURATION_HOURS: float = 24.0 * 7  # one week per seed
SIM_DURATION_MIN: float = SIM_DURATION_HOURS * 60.0
N_SEEDS: int = 30
DATA_DAYS: int = 21   # session history to build arrival distributions from


# ---------------------------------------------------------------------------
# CI helper
# ---------------------------------------------------------------------------
def _mean_ci95(values: List[float]) -> Tuple[float, float]:
    """Return (mean, half-width of 95% CI) using the t-distribution."""
    n = len(values)
    if n < 2:
        return float(np.mean(values)), 0.0
    mean = float(np.mean(values))
    se = float(np.std(values, ddof=1)) / np.sqrt(n)
    half = float(t_dist.ppf(0.975, df=n - 1)) * se
    return round(mean, 4), round(half, 4)


# ---------------------------------------------------------------------------
# Metric aggregation
# ---------------------------------------------------------------------------
def _aggregate_results(results: List[SimResult], policy_name: str) -> Dict:
    """Build a labelled summary dict for one policy across all seeds."""
    wait = [r.avg_wait_time_min for r in results]
    peak = [r.transformer_peak_kva for r in results]
    overload = [float(r.overload_intervals) for r in results]
    gini = [r.utilization_gini for r in results]
    energy = [r.energy_served_kwh for r in results]
    p95_wait = [r.p95_wait_time_min for r in results]

    w_mean, w_ci = _mean_ci95(wait)
    pk_mean, pk_ci = _mean_ci95(peak)
    ol_mean, ol_ci = _mean_ci95(overload)
    gi_mean, gi_ci = _mean_ci95(gini)
    en_mean, en_ci = _mean_ci95(energy)
    pw_mean, pw_ci = _mean_ci95(p95_wait)

    return {
        "policy": policy_name,
        "n_seeds": len(results),
        "measurement": "discrete-event simulation (SimPy)",
        "sim_duration_hours": SIM_DURATION_HOURS,
        "transformer_kva_limit": TRANSFORMER_KVA_LIMIT,
        "metrics": {
            "avg_wait_time_min": {
                "description": "[DES] Mean minutes from EV arrival to charger plug-in start",
                "mean": w_mean,
                "ci95_half_width": w_ci,
                "unit": "minutes",
            },
            "p95_wait_time_min": {
                "description": "[DES] 95th-percentile wait time across all EVs",
                "mean": pw_mean,
                "ci95_half_width": pw_ci,
                "unit": "minutes",
            },
            "transformer_peak_kva": {
                "description": "[DES] Maximum instantaneous cluster kVA (pf=0.95)",
                "mean": pk_mean,
                "ci95_half_width": pk_ci,
                "unit": "kVA",
            },
            "overload_intervals": {
                "description": "[DES] Count of 15-min windows where cluster kVA exceeded 100 kVA limit",
                "mean": ol_mean,
                "ci95_half_width": ol_ci,
                "unit": "15-min intervals",
            },
            "utilization_gini": {
                "description": "[DES] Gini coefficient of per-station utilization rates (0=perfectly equal, 1=monopoly)",
                "mean": gi_mean,
                "ci95_half_width": gi_ci,
                "unit": "dimensionless [0, 1]",
            },
            "energy_served_kwh": {
                "description": "[DES] Total energy delivered to all EVs over the simulation horizon",
                "mean": en_mean,
                "ci95_half_width": en_ci,
                "unit": "kWh",
            },
        },
    }


# ---------------------------------------------------------------------------
# Main study runner
# ---------------------------------------------------------------------------
def run_simulation_study(
    n_seeds: int = N_SEEDS,
    sim_duration_hours: float = SIM_DURATION_HOURS,
    data_days: int = DATA_DAYS,
    transformer_kva_limit: float = TRANSFORMER_KVA_LIMIT,
    out_dir: str = "../results",
    generate_charts: bool = True,
) -> Dict:
    """
    Run N seeds × 2 policies (FCFS, Smart) in discrete-event simulation.

    Returns the full summary dict (also written to results/sim_summary.json).
    """
    from app.sim.charts import generate_all_charts

    out_path = Path(out_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    sim_dur_min = sim_duration_hours * 60.0

    print("=" * 70)
    print("  EV CLUSTER LOAD — DISCRETE-EVENT SIMULATION STUDY")
    print("=" * 70)
    print(f"  Seeds: {n_seeds}  |  Duration: {sim_duration_hours}h/seed  |  Policies: FCFS, Smart")
    print(f"  Transformer limit: {transformer_kva_limit} kVA  |  Stations: {len(DEMO_STATIONS)}")
    print()

    # 1. Load session data to build empirical arrival distributions
    logger.info("Loading session data (%d days) for arrival distributions...", data_days)
    start_dt = datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc)
    acn_sessions, acn_src = fetch_acn_data(start_dt=start_dt, days=data_days)
    uev_sessions, uev_src = fetch_urbanev_data(start_dt=start_dt, days=data_days)
    all_sessions = acn_sessions + uev_sessions
    print(f"  Session sources: ACN={acn_src}, UrbanEV={uev_src}")
    print(f"  Total sessions for arrival fitting: {len(all_sessions)}")
    print()

    dist = extract_arrival_distributions(all_sessions)

    # Station configs from DEMO_STATIONS
    stations_cfg = DEMO_STATIONS
    station_ids = [s["id"] for s in stations_cfg]

    fcfs_results: List[SimResult] = []
    smart_results: List[SimResult] = []

    print(f"  Running {n_seeds} seeds × 2 policies...")
    for seed in range(1, n_seeds + 1):
        rng_fcfs = np.random.default_rng(seed * 100)
        rng_smart = np.random.default_rng(seed * 100 + 1)

        arrivals_fcfs = build_arrival_stream(dist, sim_dur_min, rng_fcfs)
        arrivals_smart = build_arrival_stream(dist, sim_dur_min, rng_smart)

        policy_fcfs = make_fcfs_policy(np.random.default_rng(seed * 100 + 2))
        policy_smart = make_smart_policy(np.random.default_rng(seed * 100 + 3))

        r_fcfs = run_one_seed(seed, policy_fcfs, arrivals_fcfs, stations_cfg, sim_dur_min, transformer_kva_limit)
        r_smart = run_one_seed(seed, policy_smart, arrivals_smart, stations_cfg, sim_dur_min, transformer_kva_limit)

        fcfs_results.append(r_fcfs)
        smart_results.append(r_smart)

        if seed % 5 == 0 or seed == 1:
            print(
                f"  Seed {seed:02d}/{n_seeds} | "
                f"FCFS wait={r_fcfs.avg_wait_time_min:.2f}min peak={r_fcfs.transformer_peak_kva:.1f}kVA | "
                f"Smart wait={r_smart.avg_wait_time_min:.2f}min peak={r_smart.transformer_peak_kva:.1f}kVA"
            )

    print()

    # 2. Aggregate metrics
    fcfs_summary = _aggregate_results(fcfs_results, "fcfs")
    smart_summary = _aggregate_results(smart_results, "smart")

    summary = {
        "title": "EV Cluster Load Discrete-Event Simulation Study",
        "measurement_note": (
            "All metrics are labelled [DES] to indicate they are measured in "
            "discrete-event simulation using SimPy. They reflect simulation behaviour "
            "under empirically bootstrapped arrival distributions and should not be "
            "extrapolated to real-world deployments without validation on live data."
        ),
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "policies": {
            "fcfs": fcfs_summary,
            "smart": smart_summary,
        },
        "comparison": _build_comparison(fcfs_summary, smart_summary),
        "chart_files": [],
    }

    # 3. Generate charts
    if generate_charts:
        chart_files = generate_all_charts(fcfs_results, smart_results, station_ids, out_path)
        summary["chart_files"] = chart_files
        print(f"  Charts written: {len(chart_files)} PNG files")

    # 4. Write JSON
    json_path = out_path / "sim_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  Summary written: {json_path}")

    # 5. Print table
    _print_comparison_table(fcfs_summary, smart_summary)

    return summary


def _build_comparison(fcfs: Dict, smart: Dict) -> Dict:
    """Build metric-by-metric comparison: improvement direction and delta."""
    comparison = {}
    metrics = list(fcfs["metrics"].keys())
    # Lower is better for: wait, overload, gini, peak; Higher is better for: energy
    lower_better = {"avg_wait_time_min", "p95_wait_time_min", "transformer_peak_kva",
                    "overload_intervals", "utilization_gini"}

    for metric in metrics:
        f_mean = fcfs["metrics"][metric]["mean"]
        s_mean = smart["metrics"][metric]["mean"]
        delta = s_mean - f_mean
        if metric in lower_better:
            smart_better = delta < 0
            change_pct = (-delta / max(abs(f_mean), 1e-9)) * 100
        else:
            smart_better = delta > 0
            change_pct = (delta / max(abs(f_mean), 1e-9)) * 100

        comparison[metric] = {
            "fcfs_mean": f_mean,
            "smart_mean": s_mean,
            "delta_smart_minus_fcfs": round(delta, 4),
            "smart_improvement_pct": round(change_pct, 2),
            "smart_wins": smart_better,
        }
    return comparison


def _print_comparison_table(fcfs: Dict, smart: Dict):
    print("=" * 90)
    print("  SIMULATION RESULTS — MEAN (95% CI) ACROSS 30 SEEDS")
    print("=" * 90)
    header = f"  {'Metric':<35} {'FCFS':>20} {'Smart':>20}"
    print(header)
    print("  " + "-" * 76)

    for key, fval in fcfs["metrics"].items():
        sval = smart["metrics"][key]
        f_str = f"{fval['mean']:.3f} ± {fval['ci95_half_width']:.3f}"
        s_str = f"{sval['mean']:.3f} ± {sval['ci95_half_width']:.3f}"
        unit = fval['unit']
        print(f"  {key:<35} {f_str:>20} {s_str:>20}  [{unit}]")

    print("=" * 90)
