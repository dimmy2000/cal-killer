"""Database session/engine factory and the `get_session` FastAPI dependency."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.event import listens_for
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


# Enable SQLite foreign keys per connection (no-op on other backends).
@listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_connection, _connection_record):  # pragma: no cover
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass


def get_session() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped SQLAlchemy session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
