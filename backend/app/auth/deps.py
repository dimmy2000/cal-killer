"""FastAPI dependencies for authentication.

`get_current_user` enforces a valid Bearer access token. Until the User model
and users table are implemented, the dependency is wired but returns a
placeholder — routes that need a real user still raise 501.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header

from app.auth.jwt import TokenError, decode_token


@dataclass
class CurrentUser:
    id: str


def get_current_user(authorization: str | None = Header(default=None)) -> CurrentUser:
    if not authorization or not authorization.lower().startswith("bearer "):
        from app.core.errors import BackendError

        raise BackendError(401, "missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        user_id = decode_token(token, "access")
    except TokenError as exc:
        from app.core.errors import BackendError

        raise BackendError(401, "invalid access token", details=str(exc)) from exc
    return CurrentUser(id=user_id)


# Re-exported as `Depends(get_current_user)` — handy alias for routes.
CurrentUserDep = Depends(get_current_user)
