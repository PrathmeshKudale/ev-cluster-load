"""Transformer resource: enforces cluster-level kVA ceiling and logs overload events.

SimPy model:
  - A shared Container tracks live kW draw across all stations.
  - Each charger process requests power from the transformer before serving
    and releases it on departure.
  - The transformer monitor samples instantaneous kVA every SAMPLE_INTERVAL_MIN
    to compute peak and overload intervals.

Power factor assumption: pf = 0.95  (kVA = kW / 0.95)
"""
from __future__ import annotations

import simpy
from typing import List


SAMPLE_INTERVAL_MIN: float = 15.0   # sample every 15 sim-minutes
POWER_FACTOR: float = 0.95          # kW → kVA conversion


class TransformerMonitor:
    """
    Monitors total active kW across the cluster at SAMPLE_INTERVAL_MIN resolution.

    Attributes
    ----------
    kva_limit : float
        Transformer nameplate kVA (default 100 kVA).
    live_kw : float
        Current instantaneous kW draw (updated by station processes).
    peak_kva : float
        Maximum observed kVA over the simulation horizon.
    overload_intervals : int
        Number of 15-min sample windows where kVA exceeded kva_limit.
    kva_trace : list[float]
        Full time-series of sampled kVA values (one per SAMPLE_INTERVAL_MIN).
    """

    def __init__(self, env: simpy.Environment, kva_limit: float = 100.0):
        self.env = env
        self.kva_limit = kva_limit
        self.live_kw: float = 0.0
        self.peak_kva: float = 0.0
        self.overload_intervals: int = 0
        self.kva_trace: List[float] = []
        # Start background monitor process
        env.process(self._monitor())

    def _monitor(self):
        while True:
            kva = self.live_kw / POWER_FACTOR
            self.kva_trace.append(kva)
            if kva > self.peak_kva:
                self.peak_kva = kva
            if kva > self.kva_limit:
                self.overload_intervals += 1
            yield self.env.timeout(SAMPLE_INTERVAL_MIN)

    def add_load(self, kw: float):
        """Called when a charging session starts."""
        self.live_kw += kw

    def remove_load(self, kw: float):
        """Called when a charging session ends or is interrupted."""
        self.live_kw = max(0.0, self.live_kw - kw)
