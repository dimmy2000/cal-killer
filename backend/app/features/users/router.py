"""Users router — `/users/me`, `/users/me/password`. Matches `interface Users`."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.deps import CurrentUser, get_current_user
from app.core.errors import BackendError
from app.features.users.schemas import PasswordChange, User, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", status_code=501)
def me(current: CurrentUser = Depends(get_current_user)) -> User:
    _ = current
    raise BackendError(501, "not implemented")


@router.patch("/me", status_code=501)
def update_me(body: UserUpdate, current: CurrentUser = Depends(get_current_user)) -> User:
    _ = body, current
    raise BackendError(501, "not implemented")


@router.patch("/me/password", status_code=501)
def change_password(body: PasswordChange, current: CurrentUser = Depends(get_current_user)) -> None:
    _ = body, current
    raise BackendError(501, "not implemented")
