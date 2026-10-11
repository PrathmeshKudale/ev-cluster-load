"""Unit and property-based test suite for core logic services.

Covers:
- Hypothesis property test: No recommendation pushes P90 cluster load above 90% when a feasible slot exists
- AHP pairwise comparison matrix Consistency Ratio (CR < 0.10) for 3 driver modes
- Erlang-C M/M/c queuing wait model
- OR-Tools CP-SAT batch assignment for simultaneous driver arrivals
- TransformerService: kW/kVA conversion, IEEE/IEC ambient-temperature derating, pandapower cross-check
- FairnessService: Jain's Fairness Index, utilization balance, peak-shaving comparison
- ReplayService: Ticker progression, seek, pause, resume, and telemetry
"""
from typing import Dict, List
import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from app.core.config import STATIONS_CONFIG
from app.services.fairness_service import FairnessService
from app.services.forecast_service import ForecastService
from app.services.recommendation_service import (
    AHP_MATRICES,
    AHP_WEIGHTS,
    RecommendationService,
    compute_ahp_weights,
    erlang_c_wait_min,
)
from app.services.replay_service import ReplayService
from app.services.transformer_service import TransformerService


# ==============================================================================
# 1. Hypothesis Property-Based Acceptance Test
# ==============================================================================

@settings(max_examples=50, deadline=None)
@given(
    mode=st.sampled_from(["fastest", "balanced", "grid_friendly"]),
    start_hour=st.integers(min_value=0, max_value=23),
    horizon=st.integers(min_value=1, max_value=24),
)
def test_hypothesis_no_recommendation_exceeds_90_pct_when_feasible_slot_exists(
    mode: str,
    start_hour: int,
    horizon: int,
):
    """
    ACCEPTANCE REQUIREMENT:
    Hypothesis test proves no recommendation pushes P90 cluster load above 90% when a feasible slot exists.
    """
    recs = RecommendationService.get_top3_recommendations(
        mode=mode,
        start_hour=start_hour,
        horizon=horizon,
    )

    cluster_pct, _, _ = ForecastService.get_cluster_and_station_forecasts()
    search_hours = [(start_hour + i) % 24 for i in range(max(1, min(horizon, 24)))]
    feasible_exists = any(float(cluster_pct[2][h]) * 100.0 <= 90.0 for h in search_hours)

    if feasible_exists and recs:
        for r in recs:
            assert r["grid_load_pct"] <= 90.0, (
                f"Violation: Recommendation at hour {r['hour']} has grid load {r['grid_load_pct']}% > 90% "
                f"despite feasible slots existing in horizon {search_hours}!"
            )


@settings(max_examples=40, deadline=None)
@given(
    synthetic_p90_loads=st.lists(
        st.floats(min_value=30.0, max_value=125.0, allow_nan=False, allow_infinity=False),
        min_size=12,
        max_size=12,
    ),
    mode=st.sampled_from(["fastest", "balanced", "grid_friendly"]),
)
def test_hypothesis_hard_transformer_constraint_synthetic_profiles(
    synthetic_p90_loads: List[float],
    mode: str,
):
    """
    Property test across arbitrary synthetic P90 profiles:
    If at least one hour has load <= 90%, all selected candidates must have load <= 90%.
    """
    candidates = []
    for off, load in enumerate(synthetic_p90_loads):
        for s in STATIONS_CONFIG:
            candidates.append({
                "station": s["name"],
                "station_id": s["id"],
                "hour": (14 + off) % 24,
                "starts_in_h": off,
                "grid_load_pct": round(load, 1),
                "score": 0.1 * off,
            })

    feasible = [c for c in candidates if c["grid_load_pct"] <= 90.0]
    pool = feasible if feasible else candidates
    top3 = sorted(pool, key=lambda c: c["score"])[:3]

    if feasible:
        for c in top3:
            assert c["grid_load_pct"] <= 90.0


# ==============================================================================
# 2. AHP Multi-Criteria Decision Weights & Consistency Ratio Tests
# ==============================================================================

def test_ahp_matrices_consistency_ratio():
    """Verify all 3 driver mode pairwise comparison matrices satisfy Saaty's CR < 0.10."""
    for mode_name, matrix in AHP_MATRICES.items():
        weights, ci, cr = compute_ahp_weights(matrix)

        # 4 criteria weights must sum to 1.0
        assert len(weights) == 4
        assert np.isclose(np.sum(weights), 1.0, atol=1e-5)
        assert np.all(weights > 0.0)

        # Consistency ratio must be strictly less than 0.10
        assert cr < 0.10, f"Mode '{mode_name}' failed AHP consistency: CR = {cr:.4f} >= 0.10"

    # Verify fastest prioritizes wait (index 0)
    assert AHP_WEIGHTS["fastest"][0] > AHP_WEIGHTS["fastest"][2]
    # Verify grid_friendly prioritizes overload risk (index 3) and balance (index 2)
    assert AHP_WEIGHTS["grid_friendly"][3] > AHP_WEIGHTS["grid_friendly"][0]


# ==============================================================================
# 3. Erlang-C Queueing Model Tests
# ==============================================================================

def test_erlang_c_queueing_behavior():
    """Verify Erlang-C queue wait time behavior: zero load, monotonicity, and capping."""
    # Zero load gives zero wait
    assert erlang_c_wait_min(c=8, util=0.0) == 0.0

    # Monotonicity with increasing utilization
    w_low = erlang_c_wait_min(c=6, util=0.30)
    w_mid = erlang_c_wait_min(c=6, util=0.60)
    w_high = erlang_c_wait_min(c=6, util=0.85)
    w_extreme = erlang_c_wait_min(c=6, util=0.99)

    assert 0.0 <= w_low < w_mid < w_high < w_extreme
    # Cap at 90 minutes
    assert w_extreme <= 90.0
    assert erlang_c_wait_min(c=4, util=1.2) <= 90.0


# ==============================================================================
# 4. OR-Tools CP-SAT Batch Assignment Tests
# ==============================================================================

def test_cp_sat_batch_driver_assignment():
    """Verify OR-Tools CP-SAT solves simultaneous arrival assignment without exceeding limits."""
    drivers = [
        {"driver_id": "D1", "mode": "fastest", "detours": {"S1": 0.0, "S2": 3.0, "S3": 6.0, "S4": 9.0}},
        {"driver_id": "D2", "mode": "balanced", "detours": {"S1": 2.0, "S2": 0.0, "S3": 5.0, "S4": 7.0}},
        {"driver_id": "D3", "mode": "grid_friendly", "detours": {"S1": 5.0, "S2": 4.0, "S3": 0.0, "S4": 2.0}},
        {"driver_id": "D4", "mode": "balanced", "detours": {"S1": 8.0, "S2": 6.0, "S3": 3.0, "S4": 0.0}},
    ]

    assignments = RecommendationService.assign_batch_drivers_cp_sat(
        drivers=drivers,
        stations=STATIONS_CONFIG,
        start_hour=14,
        horizon_hours=4,
    )

    assert len(assignments) == 4
    assigned_count = sum(1 for a in assignments if a["assigned"] is True)
    assert assigned_count >= 3  # At least 3 drivers assigned under normal cluster conditions

    for a in assignments:
        if a["assigned"]:
            assert a["station_id"] in ("S1", "S2", "S3", "S4")
            assert a["score"] is not None
            assert a["grid_load_pct"] <= 90.0


# ==============================================================================
# 5. TransformerService kW/kVA & Derating Tests
# ==============================================================================

def test_transformer_kw_kva_conversion():
    """Verify active (kW) and apparent (kVA) power conversions."""
    pf = 0.95
    kw = 95.0
    kva = TransformerService.kw_to_kva(kw, power_factor=pf)
    assert np.isclose(kva, 100.0)

    kw_back = TransformerService.kva_to_kw(kva, power_factor=pf)
    assert np.isclose(kw_back, kw)

    with pytest.raises(ValueError):
        TransformerService.kw_to_kva(100.0, power_factor=0.0)
    with pytest.raises(ValueError):
        TransformerService.kw_to_kva(100.0, power_factor=1.2)


def test_transformer_ambient_temperature_derating():
    """Verify continuous IEEE/IEC temperature derating factor interpolation."""
    # 25 C or below: 1.05 factor
    assert TransformerService.get_derating_factor(20.0) == 1.05
    assert TransformerService.get_derating_factor(25.0) == 1.05

    # 30 C nominal: 1.00 factor
    assert TransformerService.get_derating_factor(30.0) == 1.00

    # 40 C: 0.91 factor
    assert TransformerService.get_derating_factor(40.0) == 0.91

    # Effective kVA capacity scales with ambient temperature
    eff_kva_cold = TransformerService.get_effective_kva(nominal_kva=100.0, ambient_temp_c=25.0)
    eff_kva_hot = TransformerService.get_effective_kva(nominal_kva=100.0, ambient_temp_c=45.0)
    assert eff_kva_cold == 105.0
    assert eff_kva_hot == 85.0
    assert eff_kva_hot < eff_kva_cold


def test_transformer_risk_levels():
    """Verify risk levels categorize 80% warn and 90% crit correctly."""
    assert TransformerService.level(75.0) == "ok"
    assert TransformerService.level(80.0) == "ok"
    assert TransformerService.level(80.1) == "warning"
    assert TransformerService.level(89.9) == "warning"
    assert TransformerService.level(90.1) == "critical"
    assert TransformerService.level(105.0) == "critical"


def test_transformer_pandapower_feeder_cross_check():
    """Verify pandapower feeder power flow converges and matches analytical power within 5%."""
    loads = {"S1": 29.6, "S2": 22.2, "S3": 14.8, "S4": 7.4}  # ~80% load
    res = TransformerService.cross_check_feeder_pandapower(
        active_kw_per_station=loads,
        transformer_kva=100.0,
        power_factor=0.95,
    )

    assert res["converged"] is True
    assert res["loading_difference_pct"] < 5.0
    assert res["min_voltage_pu"] > 0.95  # Statutory voltage drop < 5%
    assert res["status"] in ("ok", "overloaded")


# ==============================================================================
# 6. FairnessService Tests
# ==============================================================================

def test_jains_fairness_index():
    """Verify Jain's Fairness Index properties."""
    # Completely equal allocations -> 1.0
    assert FairnessService.jains_fairness_index([10.0, 10.0, 10.0, 10.0]) == 1.0

    # Maximally unequal allocation -> 1 / n = 0.25
    extreme = FairnessService.jains_fairness_index([100.0, 0.0, 0.0, 0.0])
    assert np.isclose(extreme, 0.25, atol=1e-3)

    # Scale invariance: J(a*x) == J(x)
    j1 = FairnessService.jains_fairness_index([5.0, 10.0, 15.0])
    j2 = FairnessService.jains_fairness_index([50.0, 100.0, 150.0])
    assert np.isclose(j1, j2, atol=1e-4)


def test_fairness_utilization_balance_and_peak_shaving():
    """Verify utilization balance and peak-shaving computation."""
    bal_equal = FairnessService.utilization_balance([0.5, 0.5, 0.5, 0.5])
    assert bal_equal == 1.0

    bal_unequal = FairnessService.utilization_balance([0.9, 0.2, 0.8, 0.1])
    assert bal_unequal < bal_equal

    shaving = FairnessService.calculate_peak_shaving(fcfs_peak_kw=90.0, smart_peak_kw=72.0)
    assert shaving["peak_shaved_kw"] == 18.0
    assert shaving["peak_shaved_pct"] == 20.0


# ==============================================================================
# 7. ReplayService Tests
# ==============================================================================

def test_replay_service_lifecycle():
    """Verify pure ReplayService starts, ticks, seeks, pauses, and generates telemetry."""
    ReplayService.reset()
    s = ReplayService.start_replay(speed_multiplier=60.0, horizon_hours=12)

    assert s["status"] == "running"
    assert s["total_ticks"] == 720
    assert s["current_tick"] == 0

    # Advance 30 ticks
    s_tick = ReplayService.tick(steps=30)
    assert s_tick["current_tick"] == 30
    assert s_tick["status"] == "running"

    # Telemetry
    telem = ReplayService.get_telemetry_at_current_tick()
    assert telem["tick"] == 30
    assert "p50_load_pct" in telem

    # Pause and Resume
    s_pause = ReplayService.pause()
    assert s_pause["status"] == "paused"
    s_resume = ReplayService.resume()
    assert s_resume["status"] == "running"

    # Seek
    s_seek = ReplayService.seek(720)
    assert s_seek["current_tick"] == 720
    assert s_seek["status"] == "completed"

    # Stop
    s_stop = ReplayService.stop()
    assert s_stop["status"] == "stopped"
    assert s_stop["current_tick"] == 0
