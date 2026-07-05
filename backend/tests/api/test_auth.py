"""Smoke tests for /auth stubs — endpoints exist and return 501."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_login_stub_returns_501(client: TestClient) -> None:
    r = client.post("/auth/login", json={"email": "a@b.c", "password": "x"})
    assert r.status_code == 501, r.text


def test_register_stub_returns_501(client: TestClient) -> None:
    r = client.post(
        "/auth/register",
        json={
            "email": "a@b.c",
            "password": "x",
            "name": "A",
            "username": "a",
            "timezone": "UTC",
        },
    )
    assert r.status_code == 501, r.text


def test_refresh_stub_returns_501(client: TestClient) -> None:
    r = client.post("/auth/refresh", json={"refreshToken": "x"})
    assert r.status_code == 501, r.text


def test_logout_stub_returns_501(client: TestClient) -> None:
    r = client.post("/auth/logout", json={"refreshToken": "x"})
    assert r.status_code == 501, r.text
