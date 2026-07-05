"""FastAPI dependencies for authentication.

`get_current_user` enforces a valid Bearer access token AND that the token's
subject still exists in the database. Returns a fully-populated `CurrentUser`.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.auth.jwt import TokenError, decode_token
from app.core.errors import BackendError
from app.db.models.user import User
from app.db.session import get_session


@dataclass
class CurrentUser:
    id: str
    email: str
    name: str
    username: str
    timezone: str
    avatar_url: str | None
    created_at: str


def get_current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> CurrentUser:
    from sqlalchemy import select

    if not authorization or not authorization.lower().startswith("bearer "):
        raise BackendError(401, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_token(token, "access")
    except TokenError as exc:
        raise BackendError(401, "invalid access token", details=str(exc)) from exc

    user = session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise BackendError(401, "user not found")
    return CurrentUser(
        id=user.id,
        email=user.email,
        name=user.name,
        username=user.username,
        timezone=user.timezone,
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
    )


# Re-exported as `Depends(get_current_user)` — handy alias for routes.
CurrentUserDep = Depends(get_current_user)
