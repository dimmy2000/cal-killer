"""Tests for /public/* endpoints (no auth, manage-token gated where applicable)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def public_world(auth_client: TestClient):
    """Set up a User + Schedule + EventType for public booking tests.

    Returns a dict with the created resources and the owner's username.
    Uses the auth_client's user (testuser) as the owner.
    """
    # We need the owner's username; fetch it via /users/me.
    me = auth_client.get("/users/me").json()
    owner = me["username"]
    tz = me["timezone"]

    r = auth_client.post(
        "/schedules",
        json={
            "name": "Work",
            "timezone": tz,
            "workingHours": [
                {"dayOfWeek": 1, "startMin": 540, "endMin": 1020},  # Mon 09:00-17:00
                {"dayOfWeek": 2, "startMin": 540, "endMin": 1020},
                {"dayOfWeek": 3, "startMin": 540, "endMin": 1020},
                {"dayOfWeek": 4, "startMin": 540, "endMin": 1020},
                {"dayOfWeek": 5, "startMin": 540, "endMin": 1020},
            ],
        },
    )
    assert r.status_code == 201, r.text
    schedule = r.json()

    r = auth_client.post(
        "/event-types",
        json={
            "slug": "intro",
            "title": "Intro Call",
            "description": "A 30-minute intro",
            "durationMin": 30,
            "location": "online",
            "scheduleId": schedule["id"],
            "minNoticeMin": 120,
            "requiresConfirmation": False,
        },
    )
    assert r.status_code == 201, r.text
    event_type = r.json()

    return {
        "owner": owner,
        "owner_tz": tz,
        "schedule": schedule,
        "event_type": event_type,
    }


# ---------------------------------------------------------------------------
# P1 — GET /public/{owner}/{event}
# ---------------------------------------------------------------------------


def test_get_event_returns_projection(client: TestClient, public_world) -> None:
    r = client.get(f"/public/{public_world['owner']}/intro")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["title"] == "Intro Call"
    assert body["description"] == "A 30-minute intro"
    assert body["durationMin"] == 30
    assert body["location"] == "online"
    assert body["ownerName"] == "Test User"
    assert body["ownerTimezone"] == public_world["owner_tz"]
    assert body["requiresConfirmation"] is False


def test_get_event_unknown_owner_404(client: TestClient, public_world) -> None:
    r = client.get("/public/nosuchuser/intro")
    assert r.status_code == 404, r.text


def test_get_event_unknown_event_404(client: TestClient, public_world) -> None:
    r = client.get(f"/public/{public_world['owner']}/nosuchslug")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# P2 — GET /public/{owner}/{event}/slots
# ---------------------------------------------------------------------------


def _next_monday(tz: str = "UTC") -> datetime:
    """Return the UTC datetime of the next Monday 09:00 local-ish (just a future Monday 09:00 UTC)."""
    now = datetime.now(UTC)
    days_ahead = (7 - now.weekday()) % 7
    if days_ahead == 0 and now.hour >= 9:
        days_ahead = 7
    monday = (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday


def test_slots_basic_working_day(client: TestClient, public_world) -> None:
    """WorkingHours 09:00-17:00, duration 30 → 16 slots grid-aligned from 09:00."""
    monday = _next_monday()
    from_ = monday.isoformat()
    to = (monday + timedelta(days=1)).isoformat()
    r = client.get(
        f"/public/{public_world['owner']}/intro/slots",
        params={"from": from_, "to": to},
    )
    assert r.status_code == 200, r.text
    slots = r.json()
    # Monday 09:00-17:00 = 480 min / 30 = 16 slots
    assert len(slots) == 16
    first = datetime.fromisoformat(slots[0]["startUtc"].replace("Z", "+00:00"))
    assert first.weekday() == 0  # Monday
    assert (first.hour, first.minute) == (9, 0)


def test_slots_range_too_far_400(client: TestClient, public_world) -> None:
    now = datetime.now(UTC)
    from_ = now.isoformat()
    to = (now + timedelta(days=61)).isoformat()
    r = client.get(
        f"/public/{public_world['owner']}/intro/slots",
        params={"from": from_, "to": to},
    )
    assert r.status_code == 400, r.text


def test_slots_override_blocks_day(
    client: TestClient, public_world, auth_client: TestClient
) -> None:
    monday = _next_monday()
    date_str = monday.date().isoformat()
    auth_client.post(
        f"/schedules/{public_world['schedule']['id']}/overrides",
        json={"date": date_str, "startMin": 0, "endMin": 0, "available": False},
    )
    from_ = monday.isoformat()
    to = (monday + timedelta(days=1)).isoformat()
    r = client.get(
        f"/public/{public_world['owner']}/intro/slots",
        params={"from": from_, "to": to},
    )
    assert r.status_code == 200, r.text
    assert r.json() == []


def test_slots_min_notice_filters_close_slots(
    client: TestClient, public_world, auth_client: TestClient
) -> None:
    """minNoticeMin=120 means slots within the next 2 hours are excluded."""
    # Tighten min notice via patch.
    auth_client.patch(
        f"/event-types/{public_world['event_type']['id']}",
        json={"minNoticeMin": 120},
    )
    now = datetime.now(UTC)
    monday = _next_monday()
    # If Monday is today, near slots get filtered; just assert no slot starts
    # earlier than now+120min.
    from_ = now.isoformat()
    to = (monday + timedelta(days=7)).isoformat()
    r = client.get(
        f"/public/{public_world['owner']}/intro/slots",
        params={"from": from_, "to": to},
    )
    assert r.status_code == 200, r.text
    earliest = now + timedelta(minutes=120)
    for s in r.json():
        start = datetime.fromisoformat(s["startUtc"].replace("Z", "+00:00"))
        assert start >= earliest, (start, earliest)


def test_slots_subtracts_existing_bookings(
    client: TestClient, public_world, auth_client: TestClient, make_booking
) -> None:
    monday = _next_monday()
    slot_start = monday.replace(hour=9, minute=0, second=0, microsecond=0)
    make_booking(
        event_type_id=public_world["event_type"]["id"],
        status="confirmed",
        start_utc=slot_start,
        duration_min=30,
    )
    from_ = monday.isoformat()
    to = (monday + timedelta(days=1)).isoformat()
    r = client.get(
        f"/public/{public_world['owner']}/intro/slots",
        params={"from": from_, "to": to},
    )
    assert r.status_code == 200, r.text
    starts = [s["startUtc"] for s in r.json()]
    assert slot_start.isoformat() not in starts
    assert len(starts) == 15


# ---------------------------------------------------------------------------
# P3 — POST /public/{owner}/{event}/bookings
# ---------------------------------------------------------------------------


def test_create_booking_confirmed_no_confirmation(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["booking"]["status"] == "confirmed"
    assert body["booking"]["attendee"]["email"] == "alice@example.com"
    assert body["booking"]["location"] == "online"
    assert "manageToken" in body and isinstance(body["manageToken"], str)
    # endUtc = start + durationMin
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(body["booking"]["endUtc"].replace("Z", "+00:00"))
    assert end_dt - start_dt == timedelta(minutes=30)


def test_create_booking_pending_when_requires_confirmation(
    client: TestClient, public_world, auth_client: TestClient
) -> None:
    auth_client.patch(
        f"/event-types/{public_world['event_type']['id']}",
        json={"requiresConfirmation": True},
    )
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Bob", "email": "bob@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["booking"]["status"] == "pending"


def test_create_booking_conflict_409(client: TestClient, public_world, make_booking) -> None:
    monday = _next_monday()
    slot_start = monday.replace(hour=11, minute=0, second=0, microsecond=0)
    make_booking(
        event_type_id=public_world["event_type"]["id"],
        status="confirmed",
        start_utc=slot_start,
        duration_min=30,
    )
    r = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "C", "email": "c@example.com", "timezone": "UTC"},
            "startUtc": slot_start.isoformat(),
        },
    )
    assert r.status_code == 409, r.text


def test_create_booking_bad_grid_400(client: TestClient, public_world) -> None:
    monday = _next_monday()
    # 09:05 is not grid-aligned to 30min from 09:00 start
    start = monday.replace(hour=9, minute=5, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "D", "email": "d@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    )
    assert r.status_code == 400, r.text


def test_create_booking_too_close_min_notice_400(
    client: TestClient, public_world, auth_client: TestClient
) -> None:
    auth_client.patch(
        f"/event-types/{public_world['event_type']['id']}",
        json={"minNoticeMin": 60 * 24 * 30},  # 30 days
    )
    monday = _next_monday()
    start = monday.replace(hour=9, minute=0, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "E", "email": "e@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    )
    assert r.status_code == 400, r.text


# ---------------------------------------------------------------------------
# P4 — GET /public/bookings/{id}?token=...
# ---------------------------------------------------------------------------


def test_get_booking_with_valid_token(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]

    r = client.get(f"/public/bookings/{bid}", params={"token": token})
    assert r.status_code == 200, r.text
    assert r.json()["id"] == bid


def test_get_booking_wrong_token_401(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]

    r = client.get(f"/public/bookings/{bid}", params={"token": "wrong"})
    assert r.status_code == 401, r.text


def test_get_booking_unknown_404(client: TestClient) -> None:
    r = client.get("/public/bookings/does-not-exist", params={"token": "x"})
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# P5 — POST /public/bookings/{id}/confirm
# ---------------------------------------------------------------------------


def test_confirm_pending_to_confirmed(
    client: TestClient, public_world, auth_client: TestClient
) -> None:
    auth_client.patch(
        f"/event-types/{public_world['event_type']['id']}",
        json={"requiresConfirmation": True},
    )
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Bob", "email": "bob@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]

    r = client.post(f"/public/bookings/{bid}/confirm", json={"token": token})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "confirmed"


def test_confirm_wrong_token_401(client: TestClient, public_world, auth_client: TestClient) -> None:
    auth_client.patch(
        f"/event-types/{public_world['event_type']['id']}",
        json={"requiresConfirmation": True},
    )
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Bob", "email": "bob@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]

    r = client.post(f"/public/bookings/{bid}/confirm", json={"token": "wrong"})
    assert r.status_code == 401, r.text


def test_confirm_cancelled_409(client: TestClient, public_world, auth_client: TestClient) -> None:
    auth_client.patch(
        f"/event-types/{public_world['event_type']['id']}",
        json={"requiresConfirmation": True},
    )
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Bob", "email": "bob@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]
    client.post(f"/public/bookings/{bid}/cancel", json={"token": token})

    r = client.post(f"/public/bookings/{bid}/confirm", json={"token": token})
    assert r.status_code == 409, r.text


# ---------------------------------------------------------------------------
# P6 — POST /public/bookings/{id}/cancel
# ---------------------------------------------------------------------------


def test_cancel_booking(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]

    r = client.post(f"/public/bookings/{bid}/cancel", json={"token": token})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_wrong_token_401(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]

    r = client.post(f"/public/bookings/{bid}/cancel", json={"token": "wrong"})
    assert r.status_code == 401, r.text


def test_cancel_already_cancelled_409(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]
    client.post(f"/public/bookings/{bid}/cancel", json={"token": token})

    r = client.post(f"/public/bookings/{bid}/cancel", json={"token": token})
    assert r.status_code == 409, r.text


# ---------------------------------------------------------------------------
# P7 — POST /public/bookings/{id}/reschedule
# ---------------------------------------------------------------------------


def test_reschedule_rotates_token_and_updates_start(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    old_token = created["manageToken"]

    new_start = monday.replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/bookings/{bid}/reschedule",
        json={"token": old_token, "startUtc": new_start},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["booking"]["startUtc"] == new_start.replace("+00:00", "Z")
    assert body["manageToken"] != old_token


def test_reschedule_cancelled_409(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]
    client.post(f"/public/bookings/{bid}/cancel", json={"token": token})

    new_start = monday.replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/bookings/{bid}/reschedule",
        json={"token": token, "startUtc": new_start},
    )
    assert r.status_code == 409, r.text


def test_reschedule_conflict_409(client: TestClient, public_world, make_booking) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0)
    blocked = monday.replace(hour=12, minute=0, second=0, microsecond=0)
    make_booking(
        event_type_id=public_world["event_type"]["id"],
        status="confirmed",
        start_utc=blocked,
        duration_min=30,
    )

    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start.isoformat(),
        },
    ).json()
    bid = created["booking"]["id"]
    token = created["manageToken"]

    r = client.post(
        f"/public/bookings/{bid}/reschedule",
        json={"token": token, "startUtc": blocked.isoformat()},
    )
    assert r.status_code == 409, r.text


def test_reschedule_wrong_token_401(client: TestClient, public_world) -> None:
    monday = _next_monday()
    start = monday.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    created = client.post(
        f"/public/{public_world['owner']}/intro/bookings",
        json={
            "attendee": {"name": "Alice", "email": "alice@example.com", "timezone": "UTC"},
            "startUtc": start,
        },
    ).json()
    bid = created["booking"]["id"]

    new_start = monday.replace(hour=11, minute=0, second=0, microsecond=0).isoformat()
    r = client.post(
        f"/public/bookings/{bid}/reschedule",
        json={"token": "wrong", "startUtc": new_start},
    )
    assert r.status_code == 401, r.text
