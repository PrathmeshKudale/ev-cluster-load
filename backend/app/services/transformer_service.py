"""Transformer health monitoring service."""
from typing import Dict, Optional
from app.core.config import TRANSFORMER_KVA, WARN_THRESHOLD, CRIT_THRESHOLD
from app.services.forecast_service import ForecastService


class TransformerService:
    @staticmethod
    def level(load_pct: float) -> str:
        """Categorize load into 'ok', 'warning', or 'critical'."""
        if load_pct > CRIT_THRESHOLD * 100.0:
            return "critical"
        elif load_pct > WARN_THRESHOLD * 100.0:
            return "warning"
        return "ok"

    @classmethod
    def get_transformer_risk(cls, transformer_id: str = "T1", start_hour: int = 14) -> Dict:
        """Compute transformer peak P90 load, warning hour, and risk level."""
        forecast_data = ForecastService.format_24h_forecast(start_hour=start_hour)
        p90_series = forecast_data["p90"]
        hours = forecast_data["hours"]

        peak_p90 = max(p90_series)
        peak_idx = p90_series.index(peak_p90)
        peak_hour = hours[peak_idx]

        first_warn = next((h for h, v in zip(hours, p90_series) if v > WARN_THRESHOLD * 100.0), None)

        return {
            "transformer_id": transformer_id,
            "kva": TRANSFORMER_KVA,
            "peak_p90_pct": peak_p90,
            "peak_hour": peak_hour,
            "first_warning_hour": first_warn,
            "level": cls.level(peak_p90),
            "warn_threshold_pct": WARN_THRESHOLD * 100.0,
            "crit_threshold_pct": CRIT_THRESHOLD * 100.0,
        }
