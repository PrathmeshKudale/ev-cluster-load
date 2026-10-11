"""Base repository class providing session binding and demo mode abstraction."""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import DEMO_MODE


class BaseRepository:
    """Base class for all aggregate repositories."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.is_memory_mode = (DEMO_MODE == "memory") or (session is None)
