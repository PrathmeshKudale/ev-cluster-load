"""User aggregate repository for authentication, RBAC lookup, and user profile management."""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.db.repositories.base import BaseRepository
from app.services.user_service import UserDTO, _DEMO_USERS

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository managing User aggregate entity and authentication credentials."""

    async def get_by_username(self, username: str) -> Optional[UserDTO]:
        """Fetch user by username from DB or fallback demo store."""
        if not self.is_memory_mode and self.session:
            try:
                stmt = select(User).where(User.username == username)
                res = await self.session.execute(stmt)
                db_user = res.scalars().first()
                if db_user:
                    return UserDTO(
                        user_hash=db_user.user_hash,
                        username=db_user.username,
                        role=db_user.role,
                        cluster_id=db_user.cluster_id,
                        email=db_user.email,
                        hashed_password=db_user.hashed_password,
                        is_active=db_user.is_active,
                    )
            except Exception as exc:
                logger.warning("Error fetching user by username from DB (%s), using demo store", exc)

        return _DEMO_USERS.get(username)

    async def get_by_hash(self, user_hash: str) -> Optional[UserDTO]:
        """Fetch user by anonymized user_hash."""
        if not self.is_memory_mode and self.session:
            try:
                stmt = select(User).where(User.user_hash == user_hash)
                res = await self.session.execute(stmt)
                db_user = res.scalars().first()
                if db_user:
                    return UserDTO(
                        user_hash=db_user.user_hash,
                        username=db_user.username,
                        role=db_user.role,
                        cluster_id=db_user.cluster_id,
                        email=db_user.email,
                        hashed_password=db_user.hashed_password,
                        is_active=db_user.is_active,
                    )
            except Exception as exc:
                logger.warning("Error fetching user by hash: %s", exc)

        for u in _DEMO_USERS.values():
            if u.user_hash == user_hash:
                return u
        return None
