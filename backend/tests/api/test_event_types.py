"""Smoke tests for /event-types stubs — protected routes reject missing token."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_requires_auth(client: TestClient) -> None:
    assert client.get("/event-types").status_code == 401


def test_read_requires_auth(client: TestClient) -> None:
    assert client.get("/event-types/abc").status_code == 401
