"""Smoke tests for /public stubs — no auth, return 501."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_event_stub(client: TestClient) -> None:
    r = client.get("/public/owner/event")
    assert r.status_code == 501, r.text


def test_get_slots_stub(client: TestClient) -> None:
    r = client.get(
        "/public/owner/event/slots",
        params={"from": "2026-01-01T00:00:00Z", "to": "2026-01-02T00:00:00Z"},
    )
    assert r.status_code == 501, r.text


def test_create_booking_stub(client: TestClient) -> None:
    r = client.post(
        "/public/owner/event/bookings",
        json={
            "attendee": {"name": "A", "email": "a@b.c", "timezone": "UTC"},
            "startUtc": "2026-01-01T10:00:00Z",
        },
    )
    assert r.status_code == 501, r.text


def test_get_booking_stub(client: TestClient) -> None:
    r = client.get("/public/bookings/abc", params={"token": "t"})
    assert r.status_code == 501, r.text


def test_confirm_booking_stub(client: TestClient) -> None:
    r = client.post("/public/bookings/abc/confirm", json={"token": "t"})
    assert r.status_code == 501, r.text


def test_cancel_booking_stub(client: TestClient) -> None:
    r = client.post("/public/bookings/abc/cancel", json={"token": "t"})
    assert r.status_code == 501, r.text


def test_reschedule_booking_stub(client: TestClient) -> None:
    r = client.post(
        "/public/bookings/abc/reschedule", json={"token": "t", "startUtc": "2026-01-01T10:00:00Z"}
    )
    assert r.status_code == 501, r.text
