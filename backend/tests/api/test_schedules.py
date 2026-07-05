"""Smoke tests for /schedules stubs — protected routes reject missing token."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_requires_auth(client: TestClient) -> None:
    assert client.get("/schedules").status_code == 401


def test_create_requires_auth(client: TestClient) -> None:
    assert (
        client.post(
            "/schedules", json={"name": "x", "timezone": "UTC", "workingHours": []}
        ).status_code
        == 401
    )


def test_read_requires_auth(client: TestClient) -> None:
    assert client.get("/schedules/abc").status_code == 401


def test_list_overrides_requires_auth(client: TestClient) -> None:
    assert client.get("/schedules/abc/overrides").status_code == 401
