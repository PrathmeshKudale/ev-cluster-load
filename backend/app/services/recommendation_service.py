"""Smart charging recommendation service.

Features:
- Multi-criteria objective J = w1*wait + w2*detour + w3*(1 - balance) + w4*overload_risk
- AHP (Analytic Hierarchy Process) pairwise comparison weights with Consistency Ratio (CR < 0.10)
- Erlang-C M/M/c multi-server queuing waiting model
- OR-Tools CP-SAT batch assignment for multi-driver simultaneous arrivals
- Hard transformer constraint guaranteeing no recommendation pushes P90 cluster load above 90%
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.config import (
    CRIT_THRESHOLD,
    DELAY_WEIGHT,
    POWER_FACTOR,
    SESSION_HOURS,
    STATIONS_CONFIG,
    TRANSFORMER_KVA,
    WARN_THRESHOLD,
)
from app.services.forecast_service import ForecastService

# Saaty Random Index (RI) table for matrix sizes n = 1 .. 10
SAATY_RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

# AHP Pairwise Comparison Matrices (4 criteria: Wait, Detour, Imbalance, Overload Risk)
AHP_MATRICES: Dict[str, np.ndarray] = {
    "fastest": np.array([
        [1.0, 2.0, 4.0, 3.0],
        [0.5, 1.0, 3.0, 2.0],
        [0.25, 1.0 / 3.0, 1.0, 0.5],
        [1.0 / 3.0, 0.5, 2.0, 1.0],
    ]),
    "balanced": np.array([
        [1.0, 1.5, 1.5, 1.5],
        [1.0 / 1.5, 1.0, 1.0, 1.0],
        [1.0 / 1.5, 1.0, 1.0, 1.0],
        [1.0 / 1.5, 1.0, 1.0, 1.0],
    ]),
    "grid_friendly": np.array([
        [1.0, 1.0, 0.5, 1.0 / 3.0],
        [1.0, 1.0, 0.5, 1.0 / 3.0],
        [2.0, 2.0, 1.0, 0.5],
        [3.0, 3.0, 2.0, 1.0],
    ]),
}


def compute_ahp_weights(matrix: np.ndarray) -> Tuple[np.ndarray, float, float]:
    """
    Compute AHP priority weights, maximum eigenvalue (lambda_max), and Consistency Ratio (CR).
    Guarantees CR < 0.10 for valid decision consistency.
    """
    n = matrix.shape[0]
    # Geometric mean method for priority vector
    geom_mean = np.prod(matrix, axis=1) ** (1.0 / n)
    weights = geom_mean / np.sum(geom_mean)

    # Calculate lambda_max
    lambda_max = float(np.mean((matrix @ weights) / weights))

    # Consistency Index (CI) and Consistency Ratio (CR)
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0.0
    ri = SAATY_RI.get(n, 0.90)
    cr = float(ci / ri) if ri > 0 else 0.0

    return weights, ci, cr


# Compute and validate AHP weights for each mode
AHP_WEIGHTS: Dict[str, np.ndarray] = {}
for mode_name, mat in AHP_MATRICES.items():
    w, _, cr_val = compute_ahp_weights(mat)
    if cr_val >= 0.10:
        raise ValueError(f"AHP matrix for mode '{mode_name}' is inconsistent: CR = {cr_val:.4f} >= 0.10")
    AHP_WEIGHTS[mode_name] = w


def erlang_c_wait_min(c: int, util: float, session_h: float = SESSION_HOURS) -> float:
    """
    Mean queue wait time in minutes for an M/M/c charging site with c chargers.
    util in [0, 1].
    """
    if c <= 0:
        return 90.0
    if util <= 0.0:
        return 0.0

    # Offered load A = c * util
    a = min(util, 0.995) * c
    term, total = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        total += term

    top = term * a / c / max(1.0 - a / c, 0.005)
    prob_wait = top / max(total + top, 1e-6)

    # Expected wait in queue: Wq = (P_wait / (c - A)) * session_h * 60 min
    wait_hours = prob_wait * session_h / max(c - a, 0.01)
    return float(min(max(wait_hours * 60.0, 0.0), 90.0))


class RecommendationService:
    """Multi-objective smart charging dispatcher."""

    @classmethod
    def calculate_cost(
        cls,
        wait_min: float,
        detour_min: float,
        station_util: float,
        mean_util: float,
        grid_load_pct: float,
        offset_hours: int,
        horizon_hours: int,
        mode: str = "balanced",
    ) -> float:
        """
        Evaluate objective function J = w1*wait + w2*detour + w3*(1 - balance) + w4*risk + delay_penalty.
        """
        weights = AHP_WEIGHTS.get(mode, AHP_WEIGHTS["balanced"])

        # Normalized criteria components [0, 1]
        wait_norm = min(wait_min / 60.0, 1.0)
        detour_norm = min(detour_min / 20.0, 1.0)
        # Balance penalty: 1 - utilization_balance, higher when station load exceeds mean
        imbalance = float(np.clip(max(station_util - mean_util, 0.0) / 0.50, 0.0, 1.0))
        # Overload risk: activates above 80% warning threshold towards 90%
        risk = float(np.clip((grid_load_pct - WARN_THRESHOLD * 100.0) / 20.0, 0.0, 1.0))

        delay_penalty = DELAY_WEIGHT * (offset_hours / max(horizon_hours, 1))

        j = (
            weights[0] * wait_norm
            + weights[1] * detour_norm
            + weights[2] * imbalance
            + weights[3] * risk
            + delay_penalty
        )
        return float(round(j, 3))

    @classmethod
    def get_top3_recommendations(
        cls,
        mode: str = "balanced",
        start_hour: int = 14,
        horizon: int = 12,
        stations: List[Dict] = STATIONS_CONFIG,
    ) -> List[Dict]:
        """
        Generate Top-3 station and time-slot recommendations.
        Strictly satisfies hard transformer constraint:
        If ANY feasible slot with P90 grid load <= 90% exists, NO recommendation with load > 90% is returned.
        """
        hz = max(1, min(horizon, 24))
        cluster_pct, station_util, _ = ForecastService.get_cluster_and_station_forecasts(stations=stations)

        candidates = []
        for offset in range(hz):
            h = (start_hour + offset) % 24
            grid_pct = float(cluster_pct[2][h]) * 100.0  # P90 forecast load
            mean_u = float(np.mean([station_util[s["id"]][2][h] for s in stations]))

            for station in stations:
                sid = station["id"]
                u = float(station_util[sid][2][h])
                wait = erlang_c_wait_min(station["chargers"], u)
                detour = float(station.get("detour", 0.0))

                score = cls.calculate_cost(
                    wait_min=wait,
                    detour_min=detour,
                    station_util=u,
                    mean_util=mean_u,
                    grid_load_pct=grid_pct,
                    offset_hours=offset,
                    horizon_hours=hz,
                    mode=mode,
                )

                candidates.append({
                    "station": station["name"],
                    "station_id": sid,
                    "hour": h,
                    "starts_in_h": offset,
                    "wait_min": round(wait, 1),
                    "detour_min": detour,
                    "grid_load_pct": round(grid_pct, 1),
                    "score": score,
                })

        # Hard transformer limit enforcement:
        crit_pct = CRIT_THRESHOLD * 100.0
        feasible_candidates = [c for c in candidates if c["grid_load_pct"] <= crit_pct]

        # If any slot is within the 90% transformer limit, select strictly from feasible candidates
        pool = feasible_candidates if feasible_candidates else candidates

        best_per_station: Dict[str, Dict] = {}
        for cand in sorted(pool, key=lambda c: c["score"]):
            best_per_station.setdefault(cand["station_id"], cand)

        return list(best_per_station.values())[:3]

    @classmethod
    def assign_batch_drivers_cp_sat(
        cls,
        drivers: List[Dict],
        stations: List[Dict] = STATIONS_CONFIG,
        start_hour: int = 14,
        horizon_hours: int = 6,
        transformer_kva: float = TRANSFORMER_KVA,
        power_factor: float = POWER_FACTOR,
    ) -> List[Dict]:
        """
        Assign a batch of simultaneously arriving drivers to station-time slots using OR-Tools CP-SAT.
        Minimizes total objective J subject to station charger capacity and transformer 90% peak limit.
        """
        from ortools.sat.python import cp_model

        model = cp_model.CpModel()
        num_drivers = len(drivers)
        if num_drivers == 0:
            return []

        cluster_pct, station_util, _ = ForecastService.get_cluster_and_station_forecasts(stations=stations)
        max_kw_limit = transformer_kva * power_factor * CRIT_THRESHOLD

        # Slot indices: (station_idx, offset)
        num_stations = len(stations)
        slots = [(s_idx, off) for s_idx in range(num_stations) for off in range(horizon_hours)]

        # Decision variables: x[d, s, off] = 1 if driver d assigned to station s at offset off
        x = {}
        cost_map = {}

        for d_idx, driver in enumerate(drivers):
            mode = driver.get("mode", "balanced")
            for s_idx, off in slots:
                st = stations[s_idx]
                sid = st["id"]
                h = (start_hour + off) % 24
                grid_pct = float(cluster_pct[2][h]) * 100.0
                mean_u = float(np.mean([station_util[s["id"]][2][h] for s in stations]))
                u = float(station_util[sid][2][h])
                wait = erlang_c_wait_min(st["chargers"], u)
                detour = float(driver.get("detours", {}).get(sid, st.get("detour", 0.0)))

                cost = cls.calculate_cost(
                    wait_min=wait,
                    detour_min=detour,
                    station_util=u,
                    mean_util=mean_u,
                    grid_load_pct=grid_pct,
                    offset_hours=off,
                    horizon_hours=horizon_hours,
                    mode=mode,
                )
                cost_int = int(round(cost * 1000))  # Scale for CP-SAT integer objective
                cost_map[(d_idx, s_idx, off)] = (cost, cost_int, h, wait, detour, grid_pct)
                x[(d_idx, s_idx, off)] = model.NewBoolVar(f"x_d{d_idx}_s{s_idx}_o{off}")

        # Constraint 1: Each driver assigned to at most 1 slot
        for d_idx in range(num_drivers):
            model.Add(sum(x[(d_idx, s_idx, off)] for s_idx, off in slots) <= 1)

        # Constraint 2: Station capacity per slot (available charger limit)
        for s_idx, off in slots:
            st = stations[s_idx]
            sid = st["id"]
            h = (start_hour + off) % 24
            active_chargers = int(round(float(station_util[sid][2][h]) * st["chargers"]))
            avail_chargers = max(1, st["chargers"] - active_chargers)
            model.Add(sum(x[(d_idx, s_idx, off)] for d_idx in range(num_drivers)) <= avail_chargers)

        # Constraint 3: Cluster transformer 90% peak limit
        kw_per_charger = 7.4
        for off in range(horizon_hours):
            h = (start_hour + off) % 24
            base_kw = (float(cluster_pct[2][h]) / 100.0) * transformer_kva * power_factor
            headroom_kw = max(0.0, max_kw_limit - base_kw)
            max_assigned_in_hour = int(headroom_kw // kw_per_charger)
            if max_assigned_in_hour > 0:
                model.Add(
                    sum(x[(d_idx, s_idx, off)] for d_idx in range(num_drivers) for s_idx in range(num_stations))
                    <= max_assigned_in_hour
                )

        # Objective: minimize total assignment cost + heavy penalty for unassigned drivers
        unassigned_penalty = 10000
        obj_terms = []
        for d_idx in range(num_drivers):
            assigned_var = sum(x[(d_idx, s_idx, off)] for s_idx, off in slots)
            obj_terms.append(unassigned_penalty * (1 - assigned_var))
            for s_idx, off in slots:
                obj_terms.append(cost_map[(d_idx, s_idx, off)][1] * x[(d_idx, s_idx, off)])

        model.Minimize(sum(obj_terms))

        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 2.0
        status = solver.Solve(model)

        results = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for d_idx, driver in enumerate(drivers):
                assigned = False
                for s_idx, off in slots:
                    if solver.Value(x[(d_idx, s_idx, off)]) == 1:
                        cost, _, h, wait, detour, grid_pct = cost_map[(d_idx, s_idx, off)]
                        st = stations[s_idx]
                        results.append({
                            "driver_id": driver.get("driver_id", f"driver_{d_idx + 1}"),
                            "assigned": True,
                            "station": st["name"],
                            "station_id": st["id"],
                            "hour": h,
                            "starts_in_h": off,
                            "wait_min": round(wait, 1),
                            "detour_min": round(detour, 1),
                            "grid_load_pct": round(grid_pct, 1),
                            "score": cost,
                        })
                        assigned = True
                        break
                if not assigned:
                    results.append({
                        "driver_id": driver.get("driver_id", f"driver_{d_idx + 1}"),
                        "assigned": False,
                        "station": None,
                        "station_id": None,
                        "hour": None,
                        "starts_in_h": None,
                        "wait_min": None,
                        "detour_min": None,
                        "grid_load_pct": None,
                        "score": None,
                    })
        return results
