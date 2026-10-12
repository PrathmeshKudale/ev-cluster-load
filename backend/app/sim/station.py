"""Charging station resource for the SimPy simulation.

Each station wraps a simpy.Resource (capacity = number of chargers) and tracks:
  - Total energy served (kWh)
  - Total busy charger-minutes (for utilization rate)
  - Queue depth at each arrival event
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import simpy

from app.sim.transformer import TransformerMonitor


@dataclass
class StationStats:
    """Per-station accumulated statistics over one simulation run."""
    station_id: str
    charger_count: int
    energy_kwh: float = 0.0
    busy_charger_minutes: float = 0.0
    arrivals: int = 0
    served: int = 0
    # total simulated minutes (set by runner after sim ends)
    sim_duration_min: float = 0.0

    @property
    def utilization_rate(self) -> float:
        """Fraction of total charger-time that was in active use."""
        total_capacity_min = self.charger_count * self.sim_duration_min
        if total_capacity_min <= 0:
            return 0.0
        return min(self.busy_charger_minutes / total_capacity_min, 1.0)


class ChargingStation:
    """
    SimPy-backed charging station.

    Parameters
    ----------
    env : simpy.Environment
    station_id : str
    charger_count : int       Number of charger slots (SimPy Resource capacity).
    charger_kw : float        Per-charger power draw when active (kW).
    transformer : TransformerMonitor
    """

    def __init__(
        self,
        env: simpy.Environment,
        station_id: str,
        charger_count: int,
        charger_kw: float,
        transformer: TransformerMonitor,
        latitude: float = 0.0,
        longitude: float = 0.0,
    ):
        self.env = env
        self.station_id = station_id
        self.charger_count = charger_count
        self.charger_kw = charger_kw
        self.transformer = transformer
        self.latitude = latitude
        self.longitude = longitude

        self.resource = simpy.Resource(env, capacity=charger_count)
        self.stats = StationStats(
            station_id=station_id,
            charger_count=charger_count,
        )

    @property
    def queue_depth(self) -> int:
        """Number of EVs waiting for a charger slot right now."""
        return len(self.resource.queue)

    @property
    def active_chargers(self) -> int:
        """Number of charger slots currently in use."""
        return self.resource.count

    def serve(
        self,
        arrival_min: float,
        duration_min: float,
        energy_kwh: float,
    ):
        """
        SimPy process: request a charger, charge for duration_min, then release.

        Yields control to SimPy during wait and charge phases.
        Records metrics on the station stats object.
        """
        self.stats.arrivals += 1
        request_time = self.env.now

        with self.resource.request() as req:
            yield req  # wait for a free charger slot

            wait_min = self.env.now - request_time
            charge_start = self.env.now

            # Compute actual kW: energy_kwh / duration_h, capped at charger_kw
            duration_h = max(duration_min / 60.0, 0.01)
            actual_kw = min(energy_kwh / duration_h, self.charger_kw)

            # Register load on transformer
            self.transformer.add_load(actual_kw)

            yield self.env.timeout(duration_min)

            self.transformer.remove_load(actual_kw)

            # Accumulate station stats
            self.stats.energy_kwh += energy_kwh
            self.stats.busy_charger_minutes += duration_min
            self.stats.served += 1

        return wait_min
