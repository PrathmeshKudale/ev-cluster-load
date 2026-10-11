"""Accelerated historical and simulated replay playback service."""
import math
import time
from typing import Any, Dict, Optional


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
        from datetime import datetime, timezone

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
        # Synthetic diurnal oscillation
        diurnal_kw = 45.0 + 35.0 * math.sin(math.pi * (sim_h - 6.0) / 12.0)
        p50 = float(max(20.0, min(diurnal_kw, 95.0)))
        p10 = float(max(15.0, p50 - 12.0))
        p90 = float(min(105.0, p50 + 15.0))

        return {
            "tick": cls._current_tick,
            "simulated_hour": round(sim_h, 2),
            "p10_load_pct": round(p10, 1),
            "p50_load_pct": round(p50, 1),
            "p90_load_pct": round(p90, 1),
            "active_sessions": int(round(p50 / 8.0)),
            "status": cls._status,
        }
