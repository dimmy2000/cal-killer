"""Users router — `/users/me`, `/users/me/password`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.auth.deps import CurrentUser, get_current_user
from app.db.session import get_session
from app.features.users.schemas import PasswordChange, User, UserUpdate
from app.features.users.service import change_password, update_user

router = APIRouter(prefix="/users", tags=["Users"])


def _current_to_user(current: CurrentUser) -> User:
    return User(
        id=current.id,
        email=current.email,
        name=current.name,
        username=current.username,
        timezone=current.timezone,
        avatarUrl=current.avatar_url,
        createdAt=current.created_at,
    )


@router.get("/me")
def me(
    current: CurrentUser = Depends(get_current_user),
) -> User:
    """Return the current user's profile."""
    return _current_to_user(current)


@router.patch("/me")
def update_me(
    body: UserUpdate,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> User:
    """Update the current user's profile."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    user = update_user(session, current.id, updates)
    return user


@router.patch("/me/password", status_code=204)
def change_password_endpoint(
    body: PasswordChange,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Response:
    """Change the current user's password."""
    change_password(session, current.id, body.currentPassword, body.newPassword)
    return Response(status_code=204)
