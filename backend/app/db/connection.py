"""Database connection and session management with SQLAlchemy 2 async (asyncpg) and sync (psycopg)."""
import os
from typing import AsyncGenerator, Generator, Optional
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import (
    ASYNC_DATABASE_URL,
    DATABASE_URL,
    DEMO_MODE,
)

# Sync engine for Alembic migrations, sync scripts, and backwards compatibility
connect_args = {"connect_timeout": 2} if "psycopg" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True, connect_args=connect_args)

# Alembic & SQLAlchemy explicit constraint naming convention
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=NAMING_CONVENTION)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(metadata=metadata)

# Asynchronous engine and session factory with asyncpg
async_connect_args = {"timeout": 3} if "asyncpg" in ASYNC_DATABASE_URL else {}
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=async_connect_args,
)
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


def set_db_cluster_id(session, cluster_id: Optional[str] = None):
    """Set PostgreSQL app.cluster_id session parameter for Row-Level Security (RLS) in sync session."""
    val = cluster_id or ""
    session.execute(text("SET LOCAL app.cluster_id = :cid"), {"cid": val})


async def set_async_db_cluster_id(session: AsyncSession, cluster_id: Optional[str] = None):
    """Set PostgreSQL app.cluster_id session parameter for Row-Level Security (RLS) in async session."""
    val = cluster_id or ""
    await session.execute(text("SET LOCAL app.cluster_id = :cid"), {"cid": val})


def get_db() -> Generator:
    """FastAPI dependency for yielding synchronous database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for yielding asynchronous database sessions with automatic commit/rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_async_db_optional() -> AsyncGenerator[Optional[AsyncSession], None]:
    """FastAPI dependency yielding AsyncSession if DB is active, or None if in DEMO_MODE=memory or DB unreachable."""
    if DEMO_MODE == "memory":
        yield None
        return
    try:
        async with AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    except Exception:
        yield None


async def is_async_db_reachable() -> bool:
    """Check whether the async PostgreSQL database is reachable."""
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
            return True
    except Exception:
        return False
