from typing import Optional
from fastapi import Depends, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppException
from app.core.security import decode_token
from app.db.connection import (
    get_db,
    get_async_db,
    get_async_db_optional,
    set_db_cluster_id,
    set_async_db_cluster_id,
)
from app.db.repositories import (
    ClusterRepository,
    ForecastRepository,
    RecommendationRepository,
    SimulationRepository,
    UserRepository,
)
from app.services.user_service import UserDTO, UserService


def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> UserDTO:
    """Extract and validate Bearer access token, returning the authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AppException(
            code="UNAUTHORIZED",
            message="Authentication credentials were not provided or invalid Bearer format.",
            status_code=401,
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise AppException(
            code="INVALID_TOKEN",
            message="Invalid token type: expected access token.",
            status_code=401,
        )

    username = payload.get("sub")
    if not username:
        raise AppException(
            code="INVALID_TOKEN",
            message="Token subject missing.",
            status_code=401,
        )

    user = UserService.get_user_by_username(username, db=db)
    if not user or not user.is_active:
        raise AppException(
            code="UNAUTHORIZED",
            message="User account not found or is inactive.",
            status_code=401,
        )

    # If the user is an operator, configure PostgreSQL session RLS
    if user.role == "operator" and user.cluster_id:
        try:
            set_db_cluster_id(db, user.cluster_id)
        except Exception:
            pass

    return user


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Optional[UserDTO]:
    """Optionally extract user if Authorization header is present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        username = payload.get("sub")
        if not username:
            return None
        user = UserService.get_user_by_username(username, db=db)
        if user and user.role == "operator" and user.cluster_id:
            try:
                set_db_cluster_id(db, user.cluster_id)
            except Exception:
                pass
        return user
    except Exception:
        return None


def require_roles(*allowed_roles: str):
    """Dependency factory checking that the user has at least one of the allowed roles."""
    def role_dependency(current_user: UserDTO = Depends(get_current_user)) -> UserDTO:
        # Admin has superuser access across all endpoints
        if current_user.role == "admin":
            return current_user
        if current_user.role in allowed_roles:
            return current_user
        raise AppException(
            code="INSUFFICIENT_PERMISSIONS",
            message=f"Role '{current_user.role}' is not authorized. Required: {', '.join(allowed_roles)}",
            status_code=403,
        )
    return role_dependency


def verify_cluster_access(
    cluster_id: str,
    user: Optional[UserDTO] = None,
    db: Optional[Session] = None,
):
    """Enforce operator cluster boundary: operators may only access their own cluster."""
    if user and user.role == "operator":
        if user.cluster_id and user.cluster_id != cluster_id:
            raise AppException(
                code="CROSS_CLUSTER_ACCESS_DENIED",
                message=f"Operator is restricted to cluster '{user.cluster_id}' and cannot access cluster '{cluster_id}'.",
                status_code=403,
            )
        if db:
            try:
                set_db_cluster_id(db, user.cluster_id)
            except Exception:
                pass
    elif db:
        try:
            set_db_cluster_id(db, None)
        except Exception:
            pass


async def verify_async_cluster_access(
    cluster_id: str,
    user: Optional[UserDTO] = None,
    session: Optional[AsyncSession] = None,
):
    """Enforce operator cluster boundary in async routes."""
    if user and user.role == "operator":
        if user.cluster_id and user.cluster_id != cluster_id:
            raise AppException(
                code="CROSS_CLUSTER_ACCESS_DENIED",
                message=f"Operator is restricted to cluster '{user.cluster_id}' and cannot access cluster '{cluster_id}'.",
                status_code=403,
            )
        if session:
            try:
                await set_async_db_cluster_id(session, user.cluster_id)
            except Exception:
                pass
    elif session:
        try:
            await set_async_db_cluster_id(session, None)
        except Exception:
            pass


# ==============================================================================
# Repository Dependencies per Aggregate
# ==============================================================================

async def get_cluster_repo(
    db: Optional[AsyncSession] = Depends(get_async_db_optional),
) -> ClusterRepository:
    """Dependency injecting ClusterRepository bound to current async DB session or demo mode."""
    return ClusterRepository(session=db)


async def get_forecast_repo(
    db: Optional[AsyncSession] = Depends(get_async_db_optional),
) -> ForecastRepository:
    """Dependency injecting ForecastRepository bound to current async DB session or demo mode."""
    return ForecastRepository(session=db)


async def get_recommendation_repo(
    db: Optional[AsyncSession] = Depends(get_async_db_optional),
) -> RecommendationRepository:
    """Dependency injecting RecommendationRepository bound to current async DB session or demo mode."""
    return RecommendationRepository(session=db)


async def get_simulation_repo(
    db: Optional[AsyncSession] = Depends(get_async_db_optional),
) -> SimulationRepository:
    """Dependency injecting SimulationRepository bound to current async DB session or demo mode."""
    return SimulationRepository(session=db)


async def get_user_repo(
    db: Optional[AsyncSession] = Depends(get_async_db_optional),
) -> UserRepository:
    """Dependency injecting UserRepository bound to current async DB session or demo mode."""
    return UserRepository(session=db)

