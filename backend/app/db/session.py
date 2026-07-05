"""Database session/engine factory and the `get_session` FastAPI dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

connect_args = (
    {"check_same_thread": False} if settings.database_url_sync.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url_sync,
    connect_args=connect_args,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
