"""User ORM model — skeleton.

Columns will be added alongside the auth/users endpoint implementation.
"""

from __future__ import annotations

from app.db.base import Base


class User(Base):
    __tablename__ = "users"
