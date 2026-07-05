"""Tests for /users/me, /users/me/password."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.auth.service import hash_password
from app.db.models.user import User
from app.db.session import SessionLocal
from app.main import app


def test_me_returns_profile(auth_client: TestClient) -> None:
    """GET /users/me returns the current user's profile."""
    r = auth_client.get("/users/me")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "id" in body
    assert "email" in body
    assert "name" in body
    assert "username" in body
    assert "timezone" in body


def test_update_me_changes_fields(auth_client: TestClient) -> None:
    """PATCH /users/me updates name and timezone, verified via GET."""
    r = auth_client.patch(
        "/users/me",
        json={"name": "Updated Name", "timezone": "Asia/Tokyo"},
    )
    assert r.status_code == 200, r.text
    me_r = auth_client.get("/users/me")
    assert me_r.status_code == 200
    assert me_r.json()["name"] == "Updated Name"
    assert me_r.json()["timezone"] == "Asia/Tokyo"


def test_change_password_success_then_login_with_new(auth_client: TestClient) -> None:
    """Change password succeeds, then login with new password works."""
    # Create a fresh user with known password for this test
    session = SessionLocal()
    try:
        user = User(
            email="changepass@example.com",
            password_hash=hash_password("oldpass"),
            name="Change Pass User",
            username="changepassuser",
            timezone="UTC",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # Create auth client with this user
        token = create_access_token(user.id)
        cp = TestClient(app)
        cp.headers["Authorization"] = f"Bearer {token}"

        # Change password
        r = cp.patch(
            "/users/me/password",
            json={"currentPassword": "oldpass", "newPassword": "newpass123"},
        )
        assert r.status_code == 204, r.text

        # Login with old password fails
        r = cp.post(
            "/auth/login",
            json={"email": "changepass@example.com", "password": "oldpass"},
        )
        assert r.status_code == 401, r.text

        # Login with new password works
        r = cp.post(
            "/auth/login",
            json={"email": "changepass@example.com", "password": "newpass123"},
        )
        assert r.status_code == 200, r.text
    finally:
        session.close()


def test_update_me_duplicate_username_409(auth_client: TestClient) -> None:
    """Update me with a username already taken by another user returns 409."""
    # Create a second user
    session = SessionLocal()
    try:
        other = User(
            email="other@example.com",
            password_hash=hash_password("otherpass"),
            name="Other User",
            username="anotheruser",
            timezone="UTC",
        )
        session.add(other)
        session.commit()
        session.refresh(other)

        token = create_access_token(other.id)
        cp = TestClient(app)
        cp.headers["Authorization"] = f"Bearer {token}"

        # Try to update testuser's username to anotheruser (taken)
        r = auth_client.patch(
            "/users/me",
            json={"username": "anotheruser"},
        )
        assert r.status_code == 409, r.text
    finally:
        session.close()


def test_update_me_duplicate_email_409(auth_client: TestClient) -> None:
    """Update me with an email already taken by another user returns 409."""
    # Create a second user
    session = SessionLocal()
    try:
        other = User(
            email="other@example.com",
            password_hash=hash_password("otherpass"),
            name="Other User",
            username="anotheruser",
            timezone="UTC",
        )
        session.add(other)
        session.commit()
        session.refresh(other)

        token = create_access_token(other.id)
        cp = TestClient(app)
        cp.headers["Authorization"] = f"Bearer {token}"

        # Try to update testuser's email to other's email (taken)
        r = auth_client.patch(
            "/users/me",
            json={"email": "other@example.com"},
        )
        assert r.status_code == 409, r.text
    finally:
        session.close()
