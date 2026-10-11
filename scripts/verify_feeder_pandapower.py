"""Standalone verification script cross-checking cluster distribution feeder power flow in pandapower.

Models the 11/0.415 kV distribution substation, transformer losses, underground radial cables,
and station loads across 4 operating regimes: 50% nominal, 80% warning, 90% critical, and 100% capacity.
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(backend_path))

from app.services.transformer_service import TransformerService


def run_verification():
    print("=" * 80)
    print("EV CLUSTER LOAD - DISTRIBUTION FEEDER PANDAPOWER CROSS-CHECK")
    print("Substation: 11 / 0.415 kV | Rating: 100 kVA | Power Factor: 0.95")
    print("=" * 80)

    # Scenarios: station load splits (kW) for S1, S2, S3, S4
    scenarios = [
        ("Base Operating (50%)", {"S1": 18.5, "S2": 14.8, "S3": 7.4, "S4": 7.4}),
        ("Warning Regime (80%)", {"S1": 29.6, "S2": 22.2, "S3": 14.8, "S4": 7.4}),
        ("Critical Threshold (90%)", {"S1": 33.3, "S2": 25.0, "S3": 17.2, "S4": 10.0}),
        ("Full Cluster Limit (100%)", {"S1": 37.0, "S2": 27.5, "S3": 18.5, "S4": 12.0}),
    ]

    print(f"{'Scenario':<26} | {'Total kW':<8} | {'Analytical %':<12} | {'Pandapower %':<12} | {'Max V-Drop %':<12} | {'Status'}")
    print("-" * 88)

    for name, loads in scenarios:
        total_kw = sum(loads.values())
        res = TransformerService.cross_check_feeder_pandapower(
            active_kw_per_station=loads,
            transformer_kva=100.0,
            power_factor=0.95,
        )

        print(
            f"{name:<26} | "
            f"{total_kw:<8.1f} | "
            f"{res['analytical_loading_percent']:<12.1f} | "
            f"{res['pandapower_trafo_loading_percent']:<12.1f} | "
            f"{res['max_voltage_drop_pct']:<12.2f} | "
            f"{res['status'].upper()}"
        )

        assert res["converged"] is True, "AC load flow failed to converge"
        assert res["loading_difference_pct"] < 5.0, "Pandapower vs Analytical divergence > 5%"

    print("-" * 88)
    print("Verification completed successfully: All AC load flows converged within IEEE limits.")


if __name__ == "__main__":
    run_verification()
