"""SQLAlchemy declarative base.

All ORM models inherit from `Base`. Alembic's `env.py` targets `Base.metadata`.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
