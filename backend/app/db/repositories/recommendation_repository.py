"""Recommendation aggregate repository for Recommendation logs and history."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Recommendation
from app.db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RecommendationRepository(BaseRepository):
    """Repository managing Recommendation aggregate records."""

    async def save_recommendations(
        self,
        session_request_id: str,
        mode: str,
        top3: List[Dict],
        user_hash: Optional[str] = None,
    ) -> int:
        """Persist generated top-3 recommendations to database."""
        if self.is_memory_mode or not self.session:
            return len(top3)

        try:
            now = datetime.now(timezone.utc)
            for item in top3:
                rec_id = f"rec-{uuid.uuid4().hex[:12]}"
                rec = Recommendation(
                    id=rec_id,
                    session_request_id=session_request_id,
                    user_hash=user_hash or "anonymous_driver",
                    mode=mode,
                    recommended_station_id=item.get("station_id", item.get("station", "S1")),
                    recommended_slot_start=now,
                    rank=int(item.get("rank", 1)),
                    score=float(item.get("score", 0.0)),
                    expected_wait_min=float(item.get("expected_wait_min", item.get("wait", 0.0))),
                    expected_detour_min=float(item.get("expected_detour_min", item.get("detour", 0.0))),
                    grid_load_pct=float(item.get("grid_load_pct", 0.0)),
                    created_at=now,
                )
                self.session.add(rec)
            await self.session.flush()
            return len(top3)
        except Exception as exc:
            logger.warning("Error saving recommendations to DB (%s), continuing in-memory", exc)
            return len(top3)

    async def get_recent(
        self,
        user_hash: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict]:
        """Fetch recent recommendation records using parameterized query."""
        if self.is_memory_mode or not self.session:
            return []

        try:
            stmt = select(Recommendation)
            if user_hash:
                stmt = stmt.where(Recommendation.user_hash == user_hash)
            stmt = stmt.order_by(Recommendation.created_at.desc()).limit(limit)
            res = await self.session.execute(stmt)
            rows = res.scalars().all()
            return [
                {
                    "id": r.id,
                    "mode": r.mode,
                    "station_id": r.recommended_station_id,
                    "rank": r.rank,
                    "score": r.score,
                    "expected_wait_min": r.expected_wait_min,
                    "expected_detour_min": r.expected_detour_min,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Error querying recommendations: %s", exc)
            return []
