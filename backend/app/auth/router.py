"""Auth router — `/auth/*`."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.models import AuthTokens, LoginRequest, RefreshRequest, UserCreate
from app.auth.service import authenticate, create_user, get_user_by_id
from app.core.errors import BackendError
from app.db.session import get_session as get_db_session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(
    body: UserCreate,
    session: Any = Depends(get_db_session),
) -> AuthTokens:
    """Register a new user and return access+refresh tokens."""
    user_data = create_user(
        session=session,
        email=body.email,
        password=body.password,
        name=body.name,
        username=body.username,
        timezone=body.timezone,
        avatar_url=body.avatarUrl,
    )
    access_token = create_access_token(user_data["id"])
    refresh_token = create_refresh_token(user_data["id"])
    return AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_token,
        user=user_data,
    )


@router.post("/login")
def login(
    body: LoginRequest,
    session: Any = Depends(get_db_session),
) -> AuthTokens:
    """Exchange credentials for access+refresh tokens."""
    access_token, refresh_token, user_data = authenticate(
        email=body.email, password=body.password, session=session
    )
    return AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_token,
        user=user_data,
    )


@router.post("/refresh")
def refresh(
    body: RefreshRequest,
    session: Any = Depends(get_db_session),
) -> AuthTokens:
    """Exchange a refresh token for a new token pair."""
    try:
        user_id = decode_token(body.refreshToken, "refresh")
    except Exception:
        raise BackendError(401, "invalid refresh token") from None

    user_data = get_user_by_id(session, user_id)
    if user_data is None:
        raise BackendError(401, "user not found")

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    return AuthTokens(
        accessToken=access_token,
        refreshToken=refresh_token,
        user=user_data,
    )


@router.post("/logout", status_code=204)
def logout(body: RefreshRequest) -> Response:
    """Logout is stateless — no-op per design.

    TODO: maintain a refresh-token blacklist/revocation store so that the
    presented refresh token can actually be invalidated. Until then logout
    only clears the client's tokens; existing tokens remain valid until expiry.
    """
    _ = body
    return Response(status_code=204)
