"""Smoke tests for /bookings stubs — protected routes reject missing token."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_requires_auth(client: TestClient) -> None:
    assert client.get("/bookings").status_code == 401


def test_read_requires_auth(client: TestClient) -> None:
    assert client.get("/bookings/abc").status_code == 401


def test_cancel_requires_auth(client: TestClient) -> None:
    assert client.post("/bookings/abc/cancel").status_code == 401
