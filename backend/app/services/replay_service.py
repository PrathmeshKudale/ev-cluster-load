"""Accelerated historical and simulated replay playback service."""
import math
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.config import CRIT_THRESHOLD, STATIONS_CONFIG, WARN_THRESHOLD
from app.ml.shap_explainer import ShapExplainer


class ReplayService:
    """Pure, unit-testable simulation and historical replay engine."""

    _session_id: Optional[str] = None
    _speed_multiplier: float = 60.0
    _horizon_hours: int = 24
    _total_ticks: int = 1440  # 1 tick = 1 simulated minute (24h * 60)
    _current_tick: int = 0
    _status: str = "stopped"
    _started_at: Optional[float] = None

    @classmethod
    def reset(cls) -> None:
        """Reset internal replay state."""
        cls._session_id = None
        cls._speed_multiplier = 60.0
        cls._horizon_hours = 24
        cls._total_ticks = 1440
        cls._current_tick = 0
        cls._status = "stopped"
        cls._started_at = None

    @classmethod
    def start_replay(
        cls,
        session_id: Optional[str] = None,
        speed_multiplier: float = 60.0,
        horizon_hours: int = 24,
    ) -> Dict[str, Any]:
        """Start or restart a replay playback session."""
        cls._session_id = session_id or f"replay-{int(time.time())}"
        cls._speed_multiplier = max(1.0, min(speed_multiplier, 3600.0))
        cls._horizon_hours = max(1, min(horizon_hours, 168))
        cls._total_ticks = cls._horizon_hours * 60
        cls._current_tick = 0
        cls._status = "running"
        cls._started_at = time.time()

        return cls.get_state()

    @classmethod
    def set_speed(cls, speed_multiplier: float) -> Dict[str, Any]:
        """Update playback speed multiplier in-flight."""
        cls._speed_multiplier = max(1.0, min(speed_multiplier, 3600.0))
        return cls.get_state()

    @classmethod
    def tick(cls, steps: int = 1) -> Dict[str, Any]:
        """Advance replay by a number of simulation ticks."""
        if cls._status != "running":
            return cls.get_state()

        cls._current_tick += max(1, steps)
        if cls._current_tick >= cls._total_ticks:
            cls._current_tick = cls._total_ticks
            cls._status = "completed"

        return cls.get_state()

    @classmethod
    def seek(cls, target_tick: int) -> Dict[str, Any]:
        """Seek directly to a specific tick timestamp."""
        cls._current_tick = max(0, min(target_tick, cls._total_ticks))
        if cls._current_tick >= cls._total_ticks and cls._status == "running":
            cls._status = "completed"
        return cls.get_state()

    @classmethod
    def pause(cls) -> Dict[str, Any]:
        """Pause playback."""
        if cls._status == "running":
            cls._status = "paused"
        return cls.get_state()

    @classmethod
    def resume(cls) -> Dict[str, Any]:
        """Resume paused playback."""
        if cls._status == "paused":
            cls._status = "running"
        return cls.get_state()

    @classmethod
    def stop(cls) -> Dict[str, Any]:
        """Stop playback and reset cursor to tick 0."""
        cls._status = "stopped"
        cls._current_tick = 0
        return cls.get_state()

    @classmethod
    def get_state(cls) -> Dict[str, Any]:
        """Get snapshot of current replay playback state."""
        started_iso = (
            datetime.fromtimestamp(cls._started_at, tz=timezone.utc).isoformat()
            if cls._started_at
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "session_id": cls._session_id or f"replay-{int(time.time())}",
            "speed_multiplier": cls._speed_multiplier,
            "horizon_hours": cls._horizon_hours,
            "started_at": started_iso,
            "total_ticks": cls._total_ticks,
            "current_tick": cls._current_tick,
            "status": cls._status,
            "progress_pct": round((cls._current_tick / max(cls._total_ticks, 1)) * 100.0, 1),
            "simulated_time_h": round(cls._current_tick / 60.0, 2),
        }

    @classmethod
    def get_telemetry_at_current_tick(cls) -> Dict[str, Any]:
        """Generate dynamic cluster load telemetry corresponding to current tick."""
        sim_h = cls._current_tick / 60.0
        # Realistic diurnal pattern: morning peak at ~9am (h=9), evening peak at ~19pm (h=19)
        morning_peak = 35.0 * math.exp(-((sim_h - 9.0) ** 2) / 4.0)
        evening_peak = 48.0 * math.exp(-((sim_h - 19.0) ** 2) / 6.0)
        base_load = 28.0 + 8.0 * math.sin(math.pi * sim_h / 24.0)
        p50 = float(max(20.0, min(base_load + morning_peak + evening_peak, 96.0)))
        p10 = float(max(15.0, p50 - 10.0))
        p90 = float(min(108.0, p50 + 12.0))

        return {
            "tick": cls._current_tick,
            "simulated_hour": round(sim_h, 2),
            "p10_load_pct": round(p10, 1),
            "p50_load_pct": round(p50, 1),
            "p90_load_pct": round(p90, 1),
            "active_sessions": int(round(p50 / 8.0)),
            "status": cls._status,
        }

    @classmethod
    def get_full_frame_at_tick(cls, tick: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate full dashboard replay frame for a given tick (or current tick).
        Includes transformer load, station queues, threshold alerts, and dynamic recommendations
        with real LightGBM SHAP TreeExplainer attributions.
        """
        t = cls._current_tick if tick is None else max(0, min(tick, cls._total_ticks))
        hour = (t // 60) % 24
        minute = t % 60
        sim_h = hour + minute / 60.0

        # Diurnal load curve: baseline + morning surge (8-10am) + evening surge (17:30-20:30)
        morning_peak = 36.0 * math.exp(-((sim_h - 9.2) ** 2) / 3.5)
        evening_peak = 52.0 * math.exp(-((sim_h - 19.0) ** 2) / 5.0)
        base = 25.0 + 7.0 * math.sin(math.pi * sim_h / 24.0)
        p50 = float(max(20.0, min(base + morning_peak + evening_peak, 95.0)))
        p10 = float(max(15.0, p50 - 8.0))
        p90 = float(min(110.0, p50 + (14.0 if (8 <= hour <= 10 or 17 <= hour <= 20) else 9.0)))

        # Factor in OSCP DSO dynamic capacity limit
        from app.services.ocpp_service import OcppService
        dso_limit = OcppService.get_dso_capacity_limit(100.0)
        dso_scale = 100.0 / dso_limit if dso_limit > 0 else 1.0
        p50 = float(round(p50 * dso_scale, 1))
        p10 = float(round(p10 * dso_scale, 1))
        p90 = float(round(p90 * dso_scale, 1))

        # Determine threshold status
        warn_val = WARN_THRESHOLD * 100.0  # 80%
        crit_val = CRIT_THRESHOLD * 100.0  # 90%
        if p90 >= crit_val or dso_scale > 1.25:
            tx_status = "critical"
        elif p90 >= warn_val or dso_scale > 1.1:
            tx_status = "warning"
        else:
            tx_status = "normal"

        # Station state dynamics
        station_frames = []
        alerts = list(OcppService.get_active_alerts())
        for s in STATIONS_CONFIG:
            sid = s["id"]
            chargers = s.get("chargers", 4)
            kw_rate = s.get("kw", 7.4)
            # Station-specific diurnal weight
            pop = s.get("pop", 1.0)
            local_peak = (p50 / 100.0) * pop
            # Active bays
            occupied = max(0, min(chargers, int(round(local_peak * chargers))))
            avail = chargers - occupied
            occupancy_pct = round((occupied / max(chargers, 1)) * 100.0, 1)

            # Queue length & Erlang-C waiting time in minutes
            if avail == 0:
                # Saturated station: queue builds up
                excess = max(1, int(round((local_peak - 1.0) * chargers * 2)))
                queue_wait_min = round(float(8.0 + excess * 4.5), 1)
                queue_len = excess
            elif avail == 1 and local_peak > 0.8:
                queue_wait_min = round(float(3.5), 1)
                queue_len = 1
            else:
                queue_wait_min = 0.0
                queue_len = 0

            station_frames.append({
                "id": sid,
                "name": s["name"],
                "total_bays": chargers,
                "occupied_bays": occupied,
                "available_bays": avail,
                "occupancy_pct": occupancy_pct,
                "queue_len": queue_len,
                "queue_wait_min": queue_wait_min,
                "kw_rate": kw_rate,
            })

            # Fire station-level alert if queue wait is high
            if queue_wait_min >= 10.0:
                alerts.append({
                    "id": f"ALT-{sid}-{t}",
                    "severity": "crit",
                    "entity_type": "station",
                    "entity_id": sid,
                    "message": f"{s['name']} ({sid}) all bays full. Queue delay {queue_wait_min} min.",
                    "timestamp": f"{hour:02d}:{minute:02d} UTC",
                })

        # Transformer threshold alerts
        if tx_status == "critical":
            alerts.append({
                "id": f"ALT-TX-CRIT-{t}",
                "severity": "crit",
                "entity_type": "transformer",
                "entity_id": "T1",
                "message": f"Transformer T1 critical load! P90 forecast reached {p90:.1f}% (limit {crit_val:.0f}%).",
                "timestamp": f"{hour:02d}:{minute:02d} UTC",
            })
        elif tx_status == "warning":
            alerts.append({
                "id": f"ALT-TX-WARN-{t}",
                "severity": "warn",
                "entity_type": "transformer",
                "entity_id": "T1",
                "message": f"Transformer T1 warning! P90 forecast reached {p90:.1f}% (warn {warn_val:.0f}%).",
                "timestamp": f"{hour:02d}:{minute:02d} UTC",
            })

        # Generate adaptive recommendations based on current station congestion
        # Sort stations by least queue wait and least load
        ranked_st = sorted(
            station_frames,
            key=lambda sf: (sf["queue_wait_min"], sf["occupancy_pct"]),
        )
        recommendations = []
        for rank_idx, sf in enumerate(ranked_st[:3], start=1):
            st_cfg = next((s for s in STATIONS_CONFIG if s["id"] == sf["id"]), {})
            detour = float(st_cfg.get("detour", 0.0))
            score = round(
                0.25 * (sf["queue_wait_min"] / 15.0)
                + 0.25 * (detour / 10.0)
                + 0.25 * (sf["occupancy_pct"] / 100.0)
                + 0.25 * (p90 / 100.0),
                3,
            )

            # Compute real SHAP TreeExplainer attributions
            shap_reasons = ShapExplainer.explain_candidate(
                station_id=sf["id"],
                hour=hour,
                charger_kw=sf["kw_rate"],
                total_chargers=sf["total_bays"],
                active_sessions=sf["occupied_bays"],
            )

            recommendations.append({
                "rank": rank_idx,
                "station_id": sf["id"],
                "station_name": sf["name"],
                "hour": hour,
                "starts_in_h": 0 if sf["available_bays"] > 0 else 1,
                "available_bays": sf["available_bays"],
                "total_bays": sf["total_bays"],
                "charger_kw": sf["kw_rate"],
                "wait_min": sf["queue_wait_min"],
                "detour_min": detour,
                "grid_load_pct": round(p90, 1),
                "score": score,
                "shap_reasons": shap_reasons,
                "why_reason": (
                    f"{sf['name']} offers {sf['available_bays']} bays with {sf['queue_wait_min']} min delay. "
                    f"Grid load is {p90:.1f}% under current {tx_status.upper()} threshold."
                ),
            })

        time_str = f"{hour:02d}:{minute:02d}"
        progress_pct = round((t / max(cls._total_ticks, 1)) * 100.0, 1)

        return {
            "type": "replay_frame",
            "tick": t,
            "time_str": time_str,
            "hour": hour,
            "minute": minute,
            "progress_pct": progress_pct,
            "speed_multiplier": cls._speed_multiplier,
            "status": cls._status,
            "cluster_load_pct": round(p50, 1),
            "p10_load_pct": round(p10, 1),
            "p50_load_pct": round(p50, 1),
            "p90_load_pct": round(p90, 1),
            "transformer_status": tx_status,
            "warn_threshold_pct": warn_val,
            "crit_threshold_pct": crit_val,
            "stations": station_frames,
            "alerts": alerts,
            "recommendations": recommendations,
        }
