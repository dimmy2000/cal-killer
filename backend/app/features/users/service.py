"""Users service — get, update, change password."""

from __future__ import annotations

from app.auth.service import hash_password, verify_password
from app.core.errors import BackendError


def get_by_id(session, user_id: str) -> dict:
    """Get a user by ID."""
    from app.db.models.user import User

    user = session.get(User, user_id)
    if not user:
        raise BackendError(401, "user not found")
    return _user_to_dict(user)


def update_user(session, user_id: str, updates: dict) -> dict:
    """Update a user's fields (partial update).

    Raises BackendError(409) if email or username is already taken by another user.
    """
    from app.db.models.user import User

    user = session.get(User, user_id)
    if not user:
        raise BackendError(404, "user not found")

    for field, value in updates.items():
        if value is not None:
            setattr(user, field, value)

    # Unique checks (exclude own ID)
    if "email" in updates and updates["email"] is not None:
        existing = (
            session.query(User).filter(User.email == updates["email"], User.id != user_id).first()
        )
        if existing:
            raise BackendError(409, "email already registered")

    if "username" in updates and updates["username"] is not None:
        existing = (
            session.query(User)
            .filter(User.username == updates["username"], User.id != user_id)
            .first()
        )
        if existing:
            raise BackendError(409, "username already taken")

    session.commit()
    session.refresh(user)
    return _user_to_dict(user)


def change_password(session, user_id: str, current_password: str, new_password: str) -> None:
    """Change a user's password.

    Raises BackendError(401) if current password is incorrect.
    """
    from app.db.models.user import User

    user = session.get(User, user_id)
    if not user or not verify_password(current_password, user.password_hash):
        raise BackendError(401, "invalid current password")

    user.password_hash = hash_password(new_password)
    session.commit()


def _user_to_dict(user) -> dict:
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
