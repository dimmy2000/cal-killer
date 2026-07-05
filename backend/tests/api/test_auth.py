"""Tests for /auth/register, /auth/login, /auth/refresh, /auth/logout."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_creates_user_returns_tokens(auth_client: TestClient) -> None:
    """Register returns 201 with tokens and user data."""
    r = auth_client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "password": "strongpass123",
            "name": "New User",
            "username": "newuser",
            "timezone": "Europe/London",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "accessToken" in body
    assert "refreshToken" in body
    assert "user" in body
    assert body["user"]["id"]
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["username"] == "newuser"
    assert body["user"]["name"] == "New User"
    assert body["user"]["timezone"] == "Europe/London"

    # Access token works for /users/me
    me_r = auth_client.get("/users/me")
    assert me_r.status_code == 200, me_r.text


def test_register_duplicate_email_409(auth_client: TestClient) -> None:
    """Register with existing email returns 409."""
    r = auth_client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "password": "newpass",
            "name": "Duplicate",
            "username": "dupuser",
            "timezone": "UTC",
        },
    )
    assert r.status_code == 409, r.text


def test_register_duplicate_username_409(auth_client: TestClient) -> None:
    """Register with existing username returns 409."""
    r = auth_client.post(
        "/auth/register",
        json={
            "email": "another@example.com",
            "password": "newpass",
            "name": "Dup User",
            "username": "testuser",
            "timezone": "UTC",
        },
    )
    assert r.status_code == 409, r.text


def test_login_returns_tokens_for_valid_credentials(auth_client: TestClient) -> None:
    """Login with valid credentials returns 200 with tokens."""
    r = auth_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "accessToken" in body
    assert "refreshToken" in body
    assert "user" in body
    assert body["user"]["email"] == "test@example.com"


def test_login_wrong_password_401(auth_client: TestClient) -> None:
    """Login with wrong password returns 401."""
    r = auth_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert r.status_code == 401, r.text


def test_login_unknown_email_401(auth_client: TestClient) -> None:
    """Login with unknown email returns 401."""
    r = auth_client.post(
        "/auth/login",
        json={"email": "unknown@example.com", "password": "wrongpassword"},
    )
    assert r.status_code == 401, r.text


def test_refresh_returns_new_pair(auth_client: TestClient) -> None:
    """Refresh with valid refresh token returns new access+refresh pair."""
    # Get refresh token from login
    login_r = auth_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert login_r.status_code == 200
    body = login_r.json()
    refresh_token = body["refreshToken"]

    # Refresh
    r = auth_client.post(
        "/auth/refresh",
        json={"refreshToken": refresh_token},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "accessToken" in body
    assert "refreshToken" in body
    assert body["accessToken"] != refresh_token  # New access token


def test_refresh_with_access_token_401(auth_client: TestClient) -> None:
    """Refresh with access token (not refresh token) returns 401."""
    login_r = auth_client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert login_r.status_code == 200
    access_token = login_r.json()["accessToken"]

    r = auth_client.post(
        "/auth/refresh",
        json={"refreshToken": access_token},
    )
    assert r.status_code == 401, r.text


def test_refresh_malformed_401(auth_client: TestClient) -> None:
    """Refresh with malformed token returns 401."""
    r = auth_client.post(
        "/auth/refresh",
        json={"refreshToken": "not-a-valid-token"},
    )
    assert r.status_code == 401, r.text


def test_valid_token_unknown_user_401(auth_client: TestClient) -> None:
    """A valid access token whose subject does not exist in DB returns 401."""
    from app.auth.jwt import create_access_token

    fake_id = "00000000-0000-0000-0000-000000000000"
    token = create_access_token(fake_id)
    auth_client.headers["Authorization"] = f"Bearer {token}"

    r = auth_client.get("/users/me")
    assert r.status_code == 401, r.text


def test_logout_returns_204(auth_client: TestClient) -> None:
    """Logout is stateless and returns 204."""
    r = auth_client.post("/auth/logout", json={"refreshToken": "anything"})
    assert r.status_code == 204, r.text
