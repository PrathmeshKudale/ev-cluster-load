"""Authentication router: login, token refresh, and user profile."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.v1.schemas import LoginRequest, RefreshTokenRequest, TokenResponse, UserProfileResponse
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.errors import AppException
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.connection import get_db
from app.services.user_service import UserDTO, UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Log in with username and password")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate credentials with Argon2 and receive short-lived access and refresh tokens."""
    user = UserService.authenticate_user(request.username, request.password, db=db)
    if not user:
        raise AppException(
            code="INVALID_CREDENTIALS",
            message="Invalid username or password.",
            status_code=401,
        )

    access_token = create_access_token(
        subject=user.username,
        role=user.role,
        cluster_id=user.cluster_id,
    )
    refresh_token = create_refresh_token(
        subject=user.username,
        role=user.role,
        cluster_id=user.cluster_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfileResponse(
            username=user.username,
            role=user.role,
            cluster_id=user.cluster_id,
            email=user.email,
        ),
    )


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token")
def refresh_session(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Issue a new access and refresh token pair using an active refresh token."""
    payload = decode_token(request.refresh_token)
    if payload.get("type") != "refresh":
        raise AppException(
            code="INVALID_TOKEN_TYPE",
            message="Provided token is not a refresh token.",
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
            message="User associated with token is not active.",
            status_code=401,
        )

    access_token = create_access_token(
        subject=user.username,
        role=user.role,
        cluster_id=user.cluster_id,
    )
    new_refresh_token = create_refresh_token(
        subject=user.username,
        role=user.role,
        cluster_id=user.cluster_id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfileResponse(
            username=user.username,
            role=user.role,
            cluster_id=user.cluster_id,
            email=user.email,
        ),
    )


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
def get_me(current_user: UserDTO = Depends(get_current_user)):
    """Retrieve identity and roles for the authenticated token."""
    return UserProfileResponse(
        username=current_user.username,
        role=current_user.role,
        cluster_id=current_user.cluster_id,
        email=current_user.email,
    )
