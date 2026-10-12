"""Core SimPy simulation engine: EV arrival → dispatch → charge → depart.

Architecture
------------
  run_one_seed(seed, policy_fn, arrivals, stations_cfg, transformer_kva_limit)
    → SimResult

  The engine:
    1. Instantiates a fresh simpy.Environment + TransformerMonitor + ChargingStations.
    2. Schedules arrival events from a pre-built arrival stream (bootstrap-resampled).
    3. For each arrival: dispatch to a station via policy_fn, then start serve() process.
    4. After env.run(), collects per-station and aggregate metrics.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List

import numpy as np
import simpy

from app.sim.station import ChargingStation
from app.sim.transformer import TransformerMonitor


@dataclass
class SimResult:
    """
    Metrics from a single seed × policy run.
    All numeric labels include measurement units; all values are
    measured in discrete-event simulation (SimPy).
    """
    seed: int
    policy: str
    sim_duration_min: float

    # --- Primary metrics ---
    avg_wait_time_min: float           # [DES] mean minutes from arrival to plug-in start
    transformer_peak_kva: float        # [DES] maximum instantaneous cluster kVA
    overload_intervals: int            # [DES] count of 15-min windows with kVA > transformer_kva_limit
    utilization_gini: float            # [DES] Gini coefficient of per-station utilization rates (0=equal, 1=monopoly)
    energy_served_kwh: float           # [DES] total energy delivered to EVs

    # --- Secondary metrics ---
    total_arrivals: int                # [DES] total EV arrivals
    total_served: int                  # [DES] EVs that started charging (may be < arrivals if sim ends mid-queue)
    p95_wait_time_min: float           # [DES] 95th-percentile wait time in minutes
    utilization_rates: List[float]     # [DES] per-station utilization rates


def _gini(values: List[float]) -> float:
    """Compute Gini coefficient of a list of non-negative floats."""
    arr = sorted(values)
    n = len(arr)
    if n == 0 or sum(arr) == 0:
        return 0.0
    cumsum = 0.0
    total = sum(arr)
    gini_sum = 0.0
    for i, v in enumerate(arr):
        cumsum += v
        gini_sum += (2 * (i + 1) - n - 1) * v
    return gini_sum / (n * total)


def run_one_seed(
    seed: int,
    policy_fn: Callable,
    arrival_stream: List[Dict],
    stations_cfg: List[Dict],
    sim_duration_min: float,
    transformer_kva_limit: float = 100.0,
) -> SimResult:
    """
    Run the discrete-event simulation for a single seed and policy.

    Parameters
    ----------
    seed : int
    policy_fn : callable(arrival_dict, stations) → ChargingStation
    arrival_stream : list of dicts from arrivals.build_arrival_stream()
    stations_cfg : list of station config dicts (id, chargers, kw, latitude, longitude, detour)
    sim_duration_min : total simulation window in minutes
    transformer_kva_limit : cluster transformer nameplate kVA

    Returns
    -------
    SimResult with all metrics labelled as [DES] (discrete-event simulation).
    """
    env = simpy.Environment()
    transformer = TransformerMonitor(env, kva_limit=transformer_kva_limit)

    # Build station resources
    stations: List[ChargingStation] = []
    for cfg in stations_cfg:
        st = ChargingStation(
            env=env,
            station_id=cfg["id"],
            charger_count=cfg.get("chargers", 4),
            charger_kw=cfg.get("kw", 7.4),
            transformer=transformer,
            latitude=cfg.get("latitude", 12.97),
            longitude=cfg.get("longitude", 77.59),
        )
        st.detour_min = cfg.get("detour", 0.0)
        stations.append(st)

    # Collect per-EV wait times
    wait_times: List[float] = []

    def ev_process(arrival: Dict):
        """SimPy process for one EV: dispatch → queue → charge → depart."""
        station = policy_fn(arrival, stations)
        arrival_time = env.now
        request = station.resource.request()
        yield request

        wait = env.now - arrival_time
        wait_times.append(wait)

        # Compute charging parameters
        duration_min = arrival["duration_min"]
        energy_kwh = arrival["energy_kwh"]
        duration_h = max(duration_min / 60.0, 0.01)
        actual_kw = min(energy_kwh / duration_h, station.charger_kw)

        station.transformer.add_load(actual_kw)
        station.stats.arrivals += 1

        yield env.timeout(duration_min)

        station.transformer.remove_load(actual_kw)
        station.stats.energy_kwh += energy_kwh
        station.stats.busy_charger_minutes += duration_min
        station.stats.served += 1

        station.resource.release(request)

    def arrival_generator():
        """Schedule all pre-built arrivals as SimPy processes."""
        for arrival in arrival_stream:
            # Wait until this arrival's scheduled time
            delay = max(0.0, arrival["arrival_min"] - env.now)
            if delay > 0:
                yield env.timeout(delay)
            env.process(ev_process(arrival))
        # Yield a final timeout to allow last sessions to finish
        yield env.timeout(0)

    env.process(arrival_generator())
    env.run(until=sim_duration_min)

    # Finalise stats
    for st in stations:
        st.stats.sim_duration_min = sim_duration_min

    util_rates = [st.stats.utilization_rate for st in stations]
    total_energy = sum(st.stats.energy_kwh for st in stations)
    total_arrivals = sum(st.stats.arrivals for st in stations)
    total_served = sum(st.stats.served for st in stations)

    avg_wait = float(np.mean(wait_times)) if wait_times else 0.0
    p95_wait = float(np.percentile(wait_times, 95)) if wait_times else 0.0
    gini = _gini(util_rates)

    return SimResult(
        seed=seed,
        policy=policy_fn.__name__,
        sim_duration_min=sim_duration_min,
        avg_wait_time_min=round(avg_wait, 3),
        transformer_peak_kva=round(transformer.peak_kva, 3),
        overload_intervals=transformer.overload_intervals,
        utilization_gini=round(gini, 4),
        energy_served_kwh=round(total_energy, 2),
        total_arrivals=total_arrivals,
        total_served=total_served,
        p95_wait_time_min=round(p95_wait, 3),
        utilization_rates=[round(r, 4) for r in util_rates],
    )
