"""Auth router — `/auth/*`.

Endpoints match `interface Auth` in main.tsp. All return 501 until the
User model and password hashing are implemented.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.auth.models import AuthTokens, LoginRequest, RefreshRequest, UserCreate

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=501)
def register(body: UserCreate) -> AuthTokens:
    """Register a new user. Not implemented yet."""
    _ = body
    from app.core.errors import BackendError

    raise BackendError(501, "not implemented")


@router.post("/login", status_code=501)
def login(body: LoginRequest) -> AuthTokens:
    """Exchange credentials for access+refresh tokens. Not implemented yet."""
    _ = body
    from app.core.errors import BackendError

    raise BackendError(501, "not implemented")


@router.post("/refresh", status_code=501)
def refresh(body: RefreshRequest) -> AuthTokens:
    """Exchange a refresh token for a new token pair. Not implemented yet."""
    _ = body
    from app.core.errors import BackendError

    raise BackendError(501, "not implemented")


@router.post("/logout", status_code=501)
def logout(body: RefreshRequest) -> None:
    """Invalidate a refresh token. Not implemented yet."""
    _ = body
    from app.core.errors import BackendError

    raise BackendError(501, "not implemented")
