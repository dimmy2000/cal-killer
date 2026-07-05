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


@pytest.fixture()
def make_booking():
    """Factory that inserts a Booking (+ Attendee) directly via SessionLocal.

    Returns the Booking row as a dict (matching the API shape). Used by the
    Bookings tests to set up state without going through the (unimplemented)
    public creation endpoint.
    """

    from datetime import UTC, datetime, timedelta

    from app.auth.service import hash_password
    from app.db.models.booking import Attendee, Booking

    def _make(
        *,
        event_type_id: str,
        status: str = "pending",
        start_utc: datetime | None = None,
        duration_min: int = 30,
        location: str = "online",
        manage_token: str = "token-abc",
        attendee_name: str = "Alice",
        attendee_email: str = "alice@example.com",
        attendee_notes: str | None = None,
        attendee_timezone: str = "UTC",
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> dict:
        session = SessionLocal()
        try:
            now = datetime.now(UTC)
            start = start_utc or (now + timedelta(days=1))
            end = start + timedelta(minutes=duration_min)
            attendee = Attendee(
                name=attendee_name,
                email=attendee_email,
                notes=attendee_notes,
                timezone=attendee_timezone,
            )
            session.add(attendee)
            session.flush()
            booking = Booking(
                event_type_id=event_type_id,
                status=status,
                start_utc=start,
                end_utc=end,
                location=location,
                manage_token_hash=hash_password(manage_token),
                attendee_id=attendee.id,
                created_at=created_at or now,
                updated_at=updated_at or now,
            )
            session.add(booking)
            session.commit()
            session.refresh(booking)
            session.refresh(attendee)
            return {
                "id": booking.id,
                "status": booking.status,
                "startUtc": booking.start_utc.isoformat(),
                "endUtc": booking.end_utc.isoformat(),
                "eventTypeId": booking.event_type_id,
                "attendee": {
                    "name": attendee.name,
                    "email": attendee.email,
                    "notes": attendee.notes,
                    "timezone": attendee.timezone,
                },
                "location": booking.location,
                "createdAt": booking.created_at.isoformat(),
                "updatedAt": booking.updated_at.isoformat(),
                "_attendee_id": attendee.id,
                "_manage_token": manage_token,
            }
        finally:
            session.close()

    return _make


@pytest.fixture()
def make_event_type():
    """Factory that creates an EventType via the API under the given client.

    Wraps a Schedule + EventType so booking tests have a stable parent.
    """

    def _make(
        client,
        *,
        slug: str = "intro",
        requires_confirmation: bool = False,
        duration_min: int = 30,
        schedule_id: str | None = None,
    ) -> dict:
        if schedule_id is None:
            r = client.post(
                "/schedules",
                json={"name": "Work", "timezone": "UTC", "workingHours": []},
            )
            assert r.status_code == 201, r.text
            schedule_id = r.json()["id"]
        r = client.post(
            "/event-types",
            json={
                "slug": slug,
                "title": "Intro",
                "durationMin": duration_min,
                "location": "online",
                "scheduleId": schedule_id,
                "requiresConfirmation": requires_confirmation,
            },
        )
        assert r.status_code == 201, r.text
        return r.json()

    return _make


@pytest.fixture(autouse=True)
def cleanup_db():
    """Drop and recreate users + schedules tables before each test."""
    session = SessionLocal()
    try:
        for table in (
            "bookings",
            "attendees",
            "event_types",
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
        session.execute(
            text("""
            CREATE TABLE event_types (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(id),
                schedule_id TEXT NOT NULL REFERENCES schedules(id),
                slug TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                duration_min INTEGER NOT NULL,
                location TEXT NOT NULL,
                color TEXT,
                padding_min_before INTEGER NOT NULL DEFAULT 0,
                padding_min_after INTEGER NOT NULL DEFAULT 0,
                min_notice_min INTEGER NOT NULL DEFAULT 0,
                requires_confirmation BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                UNIQUE(user_id, slug)
            )
            """)
        )
        session.execute(
            text("""
            CREATE TABLE attendees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                notes TEXT,
                timezone TEXT NOT NULL
            )
            """)
        )
        session.execute(
            text("""
            CREATE TABLE bookings (
                id TEXT PRIMARY KEY,
                event_type_id TEXT NOT NULL REFERENCES event_types(id),
                status TEXT NOT NULL,
                start_utc TIMESTAMP NOT NULL,
                end_utc TIMESTAMP NOT NULL,
                location TEXT NOT NULL,
                manage_token_hash TEXT NOT NULL,
                attendee_id TEXT NOT NULL REFERENCES attendees(id),
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
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
