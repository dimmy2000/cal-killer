"""Auth business logic — password hashing, user creation, authentication."""

from __future__ import annotations

import bcrypt

from app.core.errors import BackendError


def hash_password(password: str) -> str:
    """Hash a password with bcrypt and return the encoded string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def user_to_dict(user) -> dict:
    """Convert a User model to a dict for JSON response."""
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "username": user.username,
        "timezone": user.timezone,
        "avatarUrl": user.avatar_url,
        "createdAt": user.created_at.isoformat(),
    }


def get_user_by_id(session, user_id: str) -> dict | None:
    """Return user dict by id, or None if not found."""
    from app.db.models.user import User

    user = session.get(User, user_id)
    return user_to_dict(user) if user else None


def create_user(
    session,
    email: str,
    password: str,
    name: str,
    username: str,
    timezone: str,
    avatar_url: str | None = None,
) -> dict:
    """Create a new user in the database.

    Returns a dict with user data (id, email, name, username, timezone, avatarUrl, createdAt).
    Raises BackendError(409) if email or username already exists.
    """
    from app.db.models.user import User

    existing_email = session.query(User).filter(User.email == email).first()
    if existing_email:
        raise BackendError(409, "email already registered")

    existing_username = session.query(User).filter(User.username == username).first()
    if existing_username:
        raise BackendError(409, "username already taken")

    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        username=username,
        timezone=timezone,
        avatar_url=avatar_url,
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    return user_to_dict(user)


def authenticate(email: str, password: str, session) -> tuple[str, str, dict]:
    """Authenticate a user by email and password.

    Returns (access_token, refresh_token, user_data).
    Raises BackendError(401) if credentials are invalid.
    """
    from app.auth.jwt import create_access_token, create_refresh_token
    from app.db.models.user import User

    user = session.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise BackendError(401, "invalid credentials")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return access_token, refresh_token, user_to_dict(user)
