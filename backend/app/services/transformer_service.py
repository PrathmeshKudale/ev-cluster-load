"""Transformer health monitoring service.

Provides:
- Active power (kW) to apparent power (kVA) conversions with power factor
- Ambient-temperature thermal derating according to IEEE C57.91 / IEC 60076-7
- 80% warning and 90% critical threshold risk assessment
- Pure, unit-testable methods and pandapower feeder cross-check
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.core.config import (
    CRIT_THRESHOLD,
    POWER_FACTOR,
    TRANSFORMER_KVA,
    WARN_THRESHOLD,
)
from app.services.forecast_service import ForecastService

# Standard IEEE/IEC ambient temperature derating reference curve
# (ambient_temp_c, derating_multiplier)
DERATING_CURVE: List[Tuple[float, float]] = [
    (25.0, 1.05),  # Cold ambient thermal headroom
    (30.0, 1.00),  # IEEE/IEC nominal reference rating (30 C)
    (35.0, 0.96),  # Mild ambient thermal derating
    (40.0, 0.91),  # Summer peak ambient derating
    (45.0, 0.85),  # Severe peak ambient derating
    (50.0, 0.77),  # Extreme heatwave emergency limit
]


class TransformerService:
    """Pure, unit-testable transformer power flow, derating, and risk assessment service."""

    @staticmethod
    def kw_to_kva(kw: float, power_factor: float = POWER_FACTOR) -> float:
        """
        Convert active power (kW) to apparent power (kVA).
        Formula: kVA = kW / power_factor
        """
        if power_factor <= 0.0 or power_factor > 1.0:
            raise ValueError(f"Power factor must be in range (0.0, 1.0], received {power_factor}")
        return float(kw / power_factor)

    @staticmethod
    def kva_to_kw(kva: float, power_factor: float = POWER_FACTOR) -> float:
        """
        Convert apparent power (kVA) to active power (kW).
        Formula: kW = kVA * power_factor
        """
        if power_factor <= 0.0 or power_factor > 1.0:
            raise ValueError(f"Power factor must be in range (0.0, 1.0], received {power_factor}")
        return float(kva * power_factor)

    @staticmethod
    def get_derating_factor(ambient_temp_c: float) -> float:
        """
        Calculate IEEE/IEC continuous thermal derating factor for a given ambient temperature.
        Interpolates piecewise between reference steps.
        """
        temps = [step[0] for step in DERATING_CURVE]
        factors = [step[1] for step in DERATING_CURVE]

        if ambient_temp_c <= temps[0]:
            return factors[0]
        if ambient_temp_c >= temps[-1]:
            # Extrapolate downwards with 0.015 / C decline, capped at 0.50
            return float(max(0.50, factors[-1] - 0.015 * (ambient_temp_c - temps[-1])))

        return float(np.interp(ambient_temp_c, temps, factors))

    @classmethod
    def get_effective_kva(cls, nominal_kva: float = TRANSFORMER_KVA, ambient_temp_c: float = 30.0) -> float:
        """Calculate temperature-derated effective transformer kVA capacity."""
        factor = cls.get_derating_factor(ambient_temp_c)
        return float(nominal_kva * factor)

    @classmethod
    def get_effective_capacity_kw(
        cls,
        nominal_kva: float = TRANSFORMER_KVA,
        ambient_temp_c: float = 30.0,
        power_factor: float = POWER_FACTOR,
    ) -> float:
        """Calculate temperature-derated maximum active power capacity in kW."""
        effective_kva = cls.get_effective_kva(nominal_kva, ambient_temp_c)
        return cls.kva_to_kw(effective_kva, power_factor)

    @staticmethod
    def level(
        load_pct: float,
        warn_threshold: float = WARN_THRESHOLD * 100.0,
        crit_threshold: float = CRIT_THRESHOLD * 100.0,
    ) -> str:
        """Categorize load percentage into 'ok', 'warning', or 'critical'."""
        if load_pct > crit_threshold:
            return "critical"
        elif load_pct > warn_threshold:
            return "warning"
        return "ok"

    @classmethod
    def get_transformer_risk(
        cls,
        transformer_id: str = "T1",
        start_hour: int = 14,
        nominal_kva: float = TRANSFORMER_KVA,
        ambient_temp_c: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Compute transformer peak P90 load, warning hour, and risk level with optional derating."""
        forecast_data = ForecastService.format_24h_forecast(start_hour=start_hour)
        p90_series = forecast_data["p90"]
        hours = forecast_data["hours"]

        # If ambient temperature is supplied, adjust thresholds to reflect derated capacity
        derating_factor = cls.get_derating_factor(ambient_temp_c) if ambient_temp_c is not None else 1.0
        effective_kva = nominal_kva * derating_factor

        # Load percentages scale inversely with derated capacity
        effective_p90 = [p / derating_factor for p in p90_series]

        peak_p90 = max(effective_p90)
        peak_idx = effective_p90.index(peak_p90)
        peak_hour = hours[peak_idx]

        warn_limit = WARN_THRESHOLD * 100.0
        first_warn = next((h for h, v in zip(hours, effective_p90) if v > warn_limit), None)

        return {
            "transformer_id": transformer_id,
            "kva": round(effective_kva, 1),
            "nominal_kva": nominal_kva,
            "derating_factor": round(derating_factor, 3),
            "peak_p90_pct": round(peak_p90, 1),
            "peak_hour": peak_hour,
            "first_warning_hour": first_warn,
            "level": cls.level(peak_p90),
            "warn_threshold_pct": warn_limit,
            "crit_threshold_pct": CRIT_THRESHOLD * 100.0,
        }

    @classmethod
    def cross_check_feeder_pandapower(
        cls,
        active_kw_per_station: Dict[str, float],
        transformer_kva: float = TRANSFORMER_KVA,
        power_factor: float = POWER_FACTOR,
        vn_hv_kv: float = 11.0,
        vn_lv_kv: float = 0.415,
    ) -> Dict[str, Any]:
        """
        Cross-check distribution feeder loading and voltage profile using pandapower AC power flow.
        Models 11/0.415 kV substation and radial LV underground lines to charging stations.
        """
        import pandapower as pp

        net = pp.create_empty_network()

        # 1. High-voltage grid slack bus and LV transformer secondary bus
        hv_bus = pp.create_bus(net, vn_kv=vn_hv_kv, name="HV_Substation_11kV")
        lv_bus = pp.create_bus(net, vn_kv=vn_lv_kv, name="LV_Substation_415V")
        pp.create_ext_grid(net, bus=hv_bus, vm_pu=1.00, name="Grid_External_Slack")

        # 2. Substation Transformer (11 / 0.415 kV)
        sn_mva = transformer_kva / 1000.0
        pp.create_transformer_from_parameters(
            net,
            hv_bus=hv_bus,
            lv_bus=lv_bus,
            sn_mva=sn_mva,
            vn_hv_kv=vn_hv_kv,
            vn_lv_kv=vn_lv_kv,
            vkr_percent=1.5,
            vk_percent=4.0,
            pfe_kw=0.3,
            i0_percent=0.2,
            name="TX_Substation",
        )

        # 3. Radial feeder lines to each EV charging station
        # Standard LV underground cable: 4x50 mm2 Cu (R=0.387 ohm/km, X=0.082 ohm/km)
        station_buses = {}
        lengths_km = {"S1": 0.15, "S2": 0.25, "S3": 0.35, "S4": 0.50}

        for sid, p_kw in active_kw_per_station.items():
            st_bus = pp.create_bus(net, vn_kv=vn_lv_kv, name=f"Bus_{sid}")
            station_buses[sid] = st_bus
            l_km = lengths_km.get(sid, 0.3)

            pp.create_line_from_parameters(
                net,
                from_bus=lv_bus,
                to_bus=st_bus,
                length_km=l_km,
                r_ohm_per_km=0.387,
                x_ohm_per_km=0.082,
                c_nf_per_km=250.0,
                max_i_ka=0.18,
                name=f"Line_LV_{sid}",
            )

            # Active (P) and Reactive (Q) power demand in MW and MVar
            p_mw = p_kw / 1000.0
            phi = np.arccos(power_factor)
            q_mvar = p_mw * np.tan(phi)
            pp.create_load(net, bus=st_bus, p_mw=p_mw, q_mvar=q_mvar, name=f"Load_{sid}")

        # Run AC power flow
        pp.runpp(net, numba=False)

        # Extract results
        trafo_loading = float(net.res_trafo.loading_percent.values[0])
        voltages_pu = {net.bus.name.iloc[i]: float(net.res_bus.vm_pu.iloc[i]) for i in range(len(net.bus))}
        min_v_pu = min(voltages_pu.values())
        max_voltage_drop_pct = float(round((1.0 - min_v_pu) * 100.0, 2))

        # Analytical kVA calculation for verification
        total_kw = sum(active_kw_per_station.values())
        analytical_kva = total_kw / power_factor
        analytical_loading_pct = (analytical_kva / transformer_kva) * 100.0

        return {
            "converged": bool(net.converged),
            "pandapower_trafo_loading_percent": round(trafo_loading, 2),
            "analytical_loading_percent": round(analytical_loading_pct, 2),
            "loading_difference_pct": round(abs(trafo_loading - analytical_loading_pct), 2),
            "bus_voltages_pu": voltages_pu,
            "min_voltage_pu": round(min_v_pu, 4),
            "max_voltage_drop_pct": max_voltage_drop_pct,
            "status": "ok" if trafo_loading <= 90.0 else "overloaded",
        }
