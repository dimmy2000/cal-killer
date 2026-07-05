"""Shared pytest fixtures.

Test database is SQLite file so each test process gets a clean database.
Tables are created manually to avoid issues with Base.metadata.create_all.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Use a file-based SQLite for tests so each process gets a clean database.
TEST_DB = BACKEND_DIR / "data" / "calkiller.test.db"
TEST_DB.parent.mkdir(parents=True, exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"

from app.auth.jwt import create_access_token  # noqa: E402
from app.auth.service import hash_password  # noqa: E402
from app.db.models.user import User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def cleanup_db():
    """Drop and recreate users + schedules tables before each test."""
    session = SessionLocal()
    try:
        for table in (
            "schedule_overrides",
            "working_hours",
            "schedules",
            "users",
        ):
            session.execute(text(f"DROP TABLE IF EXISTS {table}"))
        session.execute(
            text("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                timezone TEXT NOT NULL,
                avatar_url TEXT,
                created_at TIMESTAMP NOT NULL
            )
            """)
        )
        session.execute(
            text("""
            CREATE TABLE schedules (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                name TEXT NOT NULL,
                timezone TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """)
        )
        session.execute(
            text("""
            CREATE TABLE working_hours (
                id TEXT PRIMARY KEY,
                schedule_id TEXT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                day_of_week INTEGER NOT NULL,
                start_min INTEGER NOT NULL,
                end_min INTEGER NOT NULL,
                UNIQUE(schedule_id, day_of_week)
            )
            """)
        )
        session.execute(
            text("""
            CREATE TABLE schedule_overrides (
                id TEXT PRIMARY KEY,
                schedule_id TEXT NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
                date TEXT NOT NULL,
                start_min INTEGER NOT NULL,
                end_min INTEGER NOT NULL,
                available BOOLEAN NOT NULL,
                UNIQUE(schedule_id, date)
            )
            """)
        )
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def client() -> TestClient:
    """Bare TestClient without authentication — for 501/401 smoke tests."""
    return TestClient(app)


@pytest.fixture()
def auth_client():
    """TestClient with a registered user and a valid access token in the Authorization header."""
    client = TestClient(app)

    # Register user directly via SessionLocal (same engine as the app)
    session = SessionLocal()
    try:
        user = User(
            email="test@example.com",
            password_hash=hash_password("testpass123"),
            name="Test User",
            username="testuser",
            timezone="UTC",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = create_access_token(user.id)
        client.headers["Authorization"] = f"Bearer {token}"
    finally:
        session.close()

    yield client


@pytest.fixture()
def other_user_client():
    """Second TestClient with a different registered user — for owner-scope checks."""
    client = TestClient(app)

    session = SessionLocal()
    try:
        user = User(
            email="other@example.com",
            password_hash=hash_password("otherpass"),
            name="Other User",
            username="otheruser",
            timezone="UTC",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        token = create_access_token(user.id)
        client.headers["Authorization"] = f"Bearer {token}"
    finally:
        session.close()

    yield client
