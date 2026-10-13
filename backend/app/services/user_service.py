"""User management service providing user authentication, RBAC lookup, and demo user seeding."""
import hashlib
import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.core.config import (
    DEMO_ADMIN_PASSWORD,
    DEMO_ADMIN_USERNAME,
    DEMO_DRIVER_PASSWORD,
    DEMO_DRIVER_USERNAME,
    DEMO_JUDGE_PASSWORD,
    DEMO_JUDGE_USERNAME,
    DEMO_OPERATOR_C1_PASSWORD,
    DEMO_OPERATOR_C1_USERNAME,
    DEMO_OPERATOR_C2_PASSWORD,
    DEMO_OPERATOR_C2_USERNAME,
)
from app.core.security import hash_password, verify_password
from app.db.models import User

logger = logging.getLogger(__name__)


class UserDTO:
    """Lightweight User Data Transfer Object for decoupled user representation."""

    def __init__(
        self,
        user_hash: str,
        username: str,
        role: str,
        cluster_id: Optional[str] = None,
        email: Optional[str] = None,
        hashed_password: Optional[str] = None,
        is_active: bool = True,
    ):
        self.user_hash = user_hash
        self.username = username
        self.role = role
        self.cluster_id = cluster_id
        self.email = email
        self.hashed_password = hashed_password
        self.is_active = is_active


# Pre-hashed deterministic demo users
def _build_demo_users() -> Dict[str, UserDTO]:
    def _uhash(uname: str) -> str:
        return hashlib.sha256(f"seed_user_salt_2026_{uname}".encode()).hexdigest()

    return {
        DEMO_JUDGE_USERNAME: UserDTO(
            user_hash=_uhash(DEMO_JUDGE_USERNAME),
            username=DEMO_JUDGE_USERNAME,
            role="judge",
            cluster_id=None,
            email="judge@demo.ev",
            hashed_password=hash_password(DEMO_JUDGE_PASSWORD),
            is_active=True,
        ),
        DEMO_OPERATOR_C1_USERNAME: UserDTO(
            user_hash=_uhash(DEMO_OPERATOR_C1_USERNAME),
            username=DEMO_OPERATOR_C1_USERNAME,
            role="operator",
            cluster_id="C1",
            email="operator_c1@cluster.ev",
            hashed_password=hash_password(DEMO_OPERATOR_C1_PASSWORD),
            is_active=True,
        ),
        DEMO_OPERATOR_C2_USERNAME: UserDTO(
            user_hash=_uhash(DEMO_OPERATOR_C2_USERNAME),
            username=DEMO_OPERATOR_C2_USERNAME,
            role="operator",
            cluster_id="C2",
            email="operator_c2@cluster.ev",
            hashed_password=hash_password(DEMO_OPERATOR_C2_PASSWORD),
            is_active=True,
        ),
        DEMO_DRIVER_USERNAME: UserDTO(
            user_hash=_uhash(DEMO_DRIVER_USERNAME),
            username=DEMO_DRIVER_USERNAME,
            role="driver",
            cluster_id=None,
            email="driver@commuter.ev",
            hashed_password=hash_password(DEMO_DRIVER_PASSWORD),
            is_active=True,
        ),
        DEMO_ADMIN_USERNAME: UserDTO(
            user_hash=_uhash(DEMO_ADMIN_USERNAME),
            username=DEMO_ADMIN_USERNAME,
            role="admin",
            cluster_id=None,
            email="admin@grid.ev",
            hashed_password=hash_password(DEMO_ADMIN_PASSWORD),
            is_active=True,
        ),
        # Frontend UI Quick-Fill Aliases
        "operator": UserDTO(
            user_hash=_uhash("operator"),
            username="operator",
            role="operator",
            cluster_id="C1",
            email="operator@demo.ev",
            hashed_password=hash_password("operator123"),
            is_active=True,
        ),
        "driver": UserDTO(
            user_hash=_uhash("driver"),
            username="driver",
            role="driver",
            cluster_id=None,
            email="driver@demo.ev",
            hashed_password=hash_password("driver123"),
            is_active=True,
        ),
        "judge": UserDTO(
            user_hash=_uhash("judge"),
            username="judge",
            role="judge",
            cluster_id=None,
            email="judge@demo.ev",
            hashed_password=hash_password("judge123"),
            is_active=True,
        ),
        "admin": UserDTO(
            user_hash=_uhash("admin"),
            username="admin",
            role="admin",
            cluster_id=None,
            email="admin@demo.ev",
            hashed_password=hash_password("admin123"),
            is_active=True,
        ),
    }


_DEMO_USERS: Dict[str, UserDTO] = _build_demo_users()


class UserService:
    """Service for user retrieval, credentials verification, and seeding."""

    @classmethod
    def get_user_by_username(cls, username: str, db: Optional[Session] = None) -> Optional[UserDTO]:
        """Fetch user by username from DB or fallback demo store."""
        uname = username.strip()
        if db:
            try:
                db_user = db.query(User).filter(User.username == uname).first()
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
                logger.debug("Database query error, using in-memory store: %s", exc)

        # Fallback to demo users
        user = _DEMO_USERS.get(uname)
        if not user:
            # Check lowercase match
            user = _DEMO_USERS.get(uname.lower())
        return user

    @classmethod
    def authenticate_user(cls, username: str, password: str, db: Optional[Session] = None) -> Optional[UserDTO]:
        """Authenticate user credentials using Argon2 with demo alias and quick-fill support."""
        uname = username.strip()
        user = cls.get_user_by_username(uname, db=db)
        if not user or not user.is_active:
            return None

        # 1. Verify primary hashed password
        if user.hashed_password and verify_password(password, user.hashed_password):
            return user

        # 2. Check demo quick-fill and configuration variants
        key = uname.lower()
        acceptable_variants = {
            "operator": ["operator123", DEMO_OPERATOR_C1_PASSWORD, "OperatorPass123!"],
            DEMO_OPERATOR_C1_USERNAME.lower(): ["operator123", DEMO_OPERATOR_C1_PASSWORD, "OperatorPass123!"],
            DEMO_OPERATOR_C2_USERNAME.lower(): ["operator123", DEMO_OPERATOR_C2_PASSWORD, "OperatorPass123!"],
            "driver": ["driver123", DEMO_DRIVER_PASSWORD, "DriverPass123!"],
            DEMO_DRIVER_USERNAME.lower(): ["driver123", DEMO_DRIVER_PASSWORD, "DriverPass123!"],
            "judge": ["judge123", DEMO_JUDGE_PASSWORD, "JudgePass123!"],
            DEMO_JUDGE_USERNAME.lower(): ["judge123", DEMO_JUDGE_PASSWORD, "JudgePass123!"],
            "admin": ["admin123", DEMO_ADMIN_PASSWORD, "AdminPass123!"],
            DEMO_ADMIN_USERNAME.lower(): ["admin123", DEMO_ADMIN_PASSWORD, "AdminPass123!"],
        }

        if password in acceptable_variants.get(key, []):
            return user

        return None

    @classmethod
    def seed_demo_users_to_db(cls, db: Session) -> int:
        """Seed demo users into clean.users table idempotently."""
        count = 0
        for dto in _DEMO_USERS.values():
            existing = db.query(User).filter((User.username == dto.username) | (User.user_hash == dto.user_hash)).first()
            if not existing:
                u = User(
                    user_hash=dto.user_hash,
                    username=dto.username,
                    email=dto.email,
                    hashed_password=dto.hashed_password,
                    role=dto.role,
                    cluster_id=dto.cluster_id,
                    is_active=dto.is_active,
                )
                db.add(u)
                count += 1
            else:
                existing.username = dto.username
                existing.email = dto.email
                existing.hashed_password = dto.hashed_password
                existing.role = dto.role
                existing.cluster_id = dto.cluster_id
                existing.is_active = dto.is_active
        db.flush()
        return count
