"""Smoke tests for /users stubs — protected routes reject missing token."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_me_requires_auth(client: TestClient) -> None:
    assert client.get("/users/me").status_code == 401


def test_update_me_requires_auth(client: TestClient) -> None:
    assert client.patch("/users/me", json={"name": "x"}).status_code == 401


def test_change_password_requires_auth(client: TestClient) -> None:
    r = client.patch(
        "/users/me/password",
        json={
            "currentPassword": "a",
            "newPassword": "b",
        },
    )
    assert r.status_code == 401
