"""Forecast aggregate repository for Forecast, StationLoad, and Weather."""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import POWER_FACTOR, TRANSFORMER_KVA
from app.db.bulk_loader import CopyBulkLoader
from app.db.models import Forecast, StationLoad, Weather
from app.db.repositories.base import BaseRepository
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


class ForecastRepository(BaseRepository):
    """Repository managing stored forecasts and station load historical telemetry."""

    async def get_24h_forecast(self, cluster_id: str = "C1", start_hour: int = 14) -> Dict:
        """
        Retrieve 24-hour calibrated quantile cluster load forecast.
        In database mode, reads from clean.forecasts table; falls back to deterministic model in memory mode.
        """
        if self.is_memory_mode or not self.session:
            return ForecastService.format_24h_forecast(start_hour=start_hour)

        try:
            # Query stored forecasts from clean.forecasts table
            # Find latest issued_at timestamp
            latest_issued_stmt = select(func.max(Forecast.issued_at))
            latest_issued_res = await self.session.execute(latest_issued_stmt)
            latest_issued = latest_issued_res.scalar()

            if not latest_issued:
                # No stored forecasts in DB, use model computation
                return ForecastService.format_24h_forecast(start_hour=start_hour)

            # Query forecasts for all stations issued at latest_issued
            stmt = (
                select(Forecast)
                .where(Forecast.issued_at == latest_issued)
                .order_by(Forecast.target_ts)
            )
            result = await self.session.execute(stmt)
            records = result.scalars().all()

            if not records:
                return ForecastService.format_24h_forecast(start_hour=start_hour)

            # Group by target hour of day (0-23)
            hour_p10: Dict[int, float] = {}
            hour_p50: Dict[int, float] = {}
            hour_p90: Dict[int, float] = {}
            model_ver = records[0].model_version

            for r in records:
                hod = r.target_ts.hour
                hour_p10[hod] = hour_p10.get(hod, 0.0) + r.p10
                hour_p50[hod] = hour_p50.get(hod, 0.0) + r.p50
                hour_p90[hod] = hour_p90.get(hod, 0.0) + r.p90

            max_capacity_kw = TRANSFORMER_KVA * POWER_FACTOR
            hrs = [(start_hour + i) % 24 for i in range(24)]

            p10_list = [round((hour_p10.get(h, 25.0) / max_capacity_kw) * 100.0, 1) for h in hrs]
            p50_list = [round((hour_p50.get(h, 45.0) / max_capacity_kw) * 100.0, 1) for h in hrs]
            p90_list = [round((hour_p90.get(h, 70.0) / max_capacity_kw) * 100.0, 1) for h in hrs]

            return {
                "hours": hrs,
                "p10": p10_list,
                "p50": p50_list,
                "p90": p90_list,
                "warn": 80,
                "critical": 90,
                "model_version": model_ver,
            }
        except Exception as exc:
            logger.warning("Error fetching forecasts from DB (%s), falling back to service calculation", exc)
            return ForecastService.format_24h_forecast(start_hour=start_hour)

    async def store_forecasts(self, forecast_dicts: List[Dict]) -> int:
        """Store calibrated quantile forecasts using COPY bulk loader."""
        if not self.session or not forecast_dicts:
            return 0
        return await CopyBulkLoader.copy_forecasts(self.session, forecast_dicts)

    async def get_station_load_history(
        self,
        station_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 168,
    ) -> List[Dict]:
        """Fetch historical station load records using parameterized query."""
        if self.is_memory_mode or not self.session:
            return []

        try:
            stmt = select(StationLoad)
            if station_id:
                stmt = stmt.where(StationLoad.station_id == station_id)
            if start_time:
                stmt = stmt.where(StationLoad.timestamp >= start_time)
            if end_time:
                stmt = stmt.where(StationLoad.timestamp <= end_time)

            stmt = stmt.order_by(StationLoad.timestamp.desc()).limit(limit)
            result = await self.session.execute(stmt)
            rows = result.scalars().all()

            return [
                {
                    "station_id": r.station_id,
                    "timestamp": r.timestamp.isoformat(),
                    "active_kw": r.active_kw,
                    "active_chargers": r.active_chargers,
                    "utilization_rate": r.utilization_rate,
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Error reading station load history: %s", exc)
            return []

    async def store_station_loads(self, load_dicts: List[Dict]) -> int:
        """Store station loads using COPY bulk loader."""
        if not self.session or not load_dicts:
            return 0
        return await CopyBulkLoader.copy_station_loads(self.session, load_dicts)
