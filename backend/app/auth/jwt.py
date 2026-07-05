"""JWT encode/decode helpers for access and refresh tokens.

Token shape (claims):
- `sub`: user id (str)
- `type`: "access" | "refresh"
- `exp`, `iat`: unix timestamps (set by PyJWT)

TTLs come from `app.config.settings`.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt

from app.config import settings


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _encode(sub: str, token_type: Literal["access", "refresh"], ttl: timedelta) -> str:
    now = _now()
    payload = {
        "sub": sub,
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_access_token(user_id: str) -> str:
    return _encode(
        user_id,
        "access",
        timedelta(minutes=settings.jwt_access_ttl_minutes),
    )


def create_refresh_token(user_id: str) -> str:
    return _encode(
        user_id,
        "refresh",
        timedelta(days=settings.jwt_refresh_ttl_days),
    )


class TokenError(Exception):
    """Raised when a token is malformed, expired, or has the wrong type."""


def decode_token(token: str, expected_type: Literal["access", "refresh"]) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except jwt.PyJWTError as exc:
        raise TokenError("invalid or expired token") from exc
    sub = payload.get("sub")
    token_type = payload.get("type")
    if not isinstance(sub, str) or token_type != expected_type:
        raise TokenError("invalid token claims")
    return sub
