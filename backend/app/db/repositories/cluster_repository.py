"""Cluster aggregate repository for Cluster, Transformer, Station, and Charger."""
import logging
from typing import Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import POWER_FACTOR, STATIONS_CONFIG, TRANSFORMER_KVA
from app.db.models import Charger, Cluster, Station, Transformer
from app.db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ClusterRepository(BaseRepository):
    """Repository managing Cluster aggregate root and associated grid entities."""

    async def get_cluster_topology(self, cluster_id: str = "C1") -> Dict:
        """
        Retrieve cluster topology, transformer electrical rating, and connected stations.
        Returns identical shape in both database and in-memory demo modes.
        """
        if self.is_memory_mode or not self.session:
            return {
                "transformer_kva": TRANSFORMER_KVA,
                "power_factor": POWER_FACTOR,
                "stations": STATIONS_CONFIG,
            }

        try:
            # Query transformer for this cluster using parameterized SQLAlchemy 2 statement
            trafo_stmt = (
                select(Transformer)
                .where(Transformer.cluster_id == cluster_id)
                .order_by(Transformer.id)
            )
            trafo_result = await self.session.execute(trafo_stmt)
            trafo = trafo_result.scalars().first()

            rating_kva = trafo.rating_kva if trafo else TRANSFORMER_KVA
            pf = trafo.power_factor if trafo else POWER_FACTOR

            # Query stations connected to this cluster
            station_stmt = (
                select(Station)
                .where(Station.cluster_id == cluster_id)
                .order_by(Station.id)
            )
            station_result = await self.session.execute(station_stmt)
            stations = station_result.scalars().all()

            if not stations:
                return {
                    "transformer_kva": rating_kva,
                    "power_factor": pf,
                    "stations": STATIONS_CONFIG,
                }

            # For each station, count chargers and find max_kw
            station_dicts = []
            for s in stations:
                charger_stmt = select(
                    func.count(Charger.id),
                    func.coalesce(func.max(Charger.max_kw), 7.4)
                ).where(Charger.station_id == s.id)
                charger_res = await self.session.execute(charger_stmt)
                count, max_kw = charger_res.first()

                station_dicts.append({
                    "id": s.id,
                    "name": s.name,
                    "chargers": count if count > 0 else 4,
                    "kw": float(max_kw) if max_kw else 7.4,
                    "detour": float(s.detour_min),
                    "latitude": float(s.latitude),
                    "longitude": float(s.longitude),
                })

            return {
                "transformer_kva": rating_kva,
                "power_factor": pf,
                "stations": station_dicts,
            }
        except Exception as exc:
            logger.warning("Error fetching cluster topology from DB (%s), using demo store", exc)
            return {
                "transformer_kva": TRANSFORMER_KVA,
                "power_factor": POWER_FACTOR,
                "stations": STATIONS_CONFIG,
            }

    async def list_stations(
        self,
        cluster_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Dict], int]:
        """
        Retrieve paginated stations list.
        Returns: (station_list, total_count)
        """
        if self.is_memory_mode or not self.session:
            total_items = len(STATIONS_CONFIG)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            return STATIONS_CONFIG[start_idx:end_idx], total_items

        try:
            query = select(Station)
            count_query = select(func.count(Station.id))
            if cluster_id:
                query = query.where(Station.cluster_id == cluster_id)
                count_query = count_query.where(Station.cluster_id == cluster_id)

            total_res = await self.session.execute(count_query)
            total_items = total_res.scalar() or 0

            if total_items == 0:
                total_items = len(STATIONS_CONFIG)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                return STATIONS_CONFIG[start_idx:end_idx], total_items

            offset_val = (page - 1) * page_size
            query = query.order_by(Station.id).offset(offset_val).limit(page_size)
            result = await self.session.execute(query)
            stations = result.scalars().all()

            station_dicts = []
            for s in stations:
                charger_stmt = select(
                    func.count(Charger.id),
                    func.coalesce(func.max(Charger.max_kw), 7.4)
                ).where(Charger.station_id == s.id)
                charger_res = await self.session.execute(charger_stmt)
                count, max_kw = charger_res.first()

                station_dicts.append({
                    "id": s.id,
                    "name": s.name,
                    "chargers": count if count > 0 else 4,
                    "kw": float(max_kw) if max_kw else 7.4,
                    "detour": float(s.detour_min),
                    "latitude": float(s.latitude),
                    "longitude": float(s.longitude),
                })

            return station_dicts, total_items
        except Exception as exc:
            logger.warning("Error fetching stations from DB (%s), using demo store", exc)
            total_items = len(STATIONS_CONFIG)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            return STATIONS_CONFIG[start_idx:end_idx], total_items

    async def get_transformer(self, transformer_id: str = "T1") -> Optional[Dict]:
        """Retrieve transformer electrical parameters."""
        if self.is_memory_mode or not self.session:
            return {
                "id": transformer_id,
                "rating_kva": TRANSFORMER_KVA,
                "power_factor": POWER_FACTOR,
                "warn_threshold_pct": 0.80,
                "crit_threshold_pct": 0.90,
            }

        try:
            stmt = select(Transformer).where(Transformer.id == transformer_id)
            res = await self.session.execute(stmt)
            trafo = res.scalars().first()
            if trafo:
                return {
                    "id": trafo.id,
                    "rating_kva": trafo.rating_kva,
                    "power_factor": trafo.power_factor,
                    "warn_threshold_pct": trafo.warn_threshold_pct,
                    "crit_threshold_pct": trafo.crit_threshold_pct,
                }
        except Exception as exc:
            logger.warning("Error fetching transformer (%s), using defaults", exc)

        return {
            "id": transformer_id,
            "rating_kva": TRANSFORMER_KVA,
            "power_factor": POWER_FACTOR,
            "warn_threshold_pct": 0.80,
            "crit_threshold_pct": 0.90,
        }
