"""Tests for /bookings (owner-side)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# B1 — GET /bookings (200)
# ---------------------------------------------------------------------------


def test_list_requires_auth(client: TestClient) -> None:
    assert client.get("/bookings").status_code == 401


def test_list_returns_only_own_bookings(
    auth_client: TestClient,
    other_user_client: TestClient,
    make_event_type,
    make_booking,
) -> None:
    et_a = make_event_type(auth_client)
    et_b = make_event_type(other_user_client)
    mine = make_booking(event_type_id=et_a["id"])["id"]
    make_booking(event_type_id=et_b["id"])

    r = auth_client.get("/bookings")
    assert r.status_code == 200, r.text
    ids = [b["id"] for b in r.json()["items"]]
    assert ids == [mine]


def test_list_filter_by_status(auth_client: TestClient, make_event_type, make_booking) -> None:
    et = make_event_type(auth_client)
    pending = make_booking(event_type_id=et["id"], status="pending")
    confirmed = make_booking(event_type_id=et["id"], status="confirmed")
    cancelled = make_booking(event_type_id=et["id"], status="cancelled")

    r = auth_client.get("/bookings?status=confirmed")
    assert r.status_code == 200, r.text
    ids = {b["id"] for b in r.json()["items"]}
    assert ids == {confirmed["id"]}
    assert pending["id"] not in ids
    assert cancelled["id"] not in ids


def test_list_filter_by_event_type_id(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et1 = make_event_type(auth_client, slug="a")
    et2 = make_event_type(auth_client, slug="b")
    b1 = make_booking(event_type_id=et1["id"])
    b2 = make_booking(event_type_id=et2["id"])

    r = auth_client.get(f"/bookings?eventTypeId={et1['id']}")
    assert r.status_code == 200, r.text
    ids = {b["id"] for b in r.json()["items"]}
    assert ids == {b1["id"]}
    assert b2["id"] not in ids


def test_list_filter_by_attendee_email(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    a = make_booking(event_type_id=et["id"], attendee_email="alice@example.com")
    b = make_booking(event_type_id=et["id"], attendee_email="bob@example.com")

    r = auth_client.get("/bookings?attendeeEmail=alice@example.com")
    assert r.status_code == 200, r.text
    ids = {x["id"] for x in r.json()["items"]}
    assert ids == {a["id"]}
    assert b["id"] not in ids


def test_list_filter_by_from_to(auth_client: TestClient, make_event_type, make_booking) -> None:
    et = make_event_type(auth_client)
    now = datetime.now(UTC)
    past = make_booking(event_type_id=et["id"], start_utc=now - timedelta(days=5))
    in_range = make_booking(event_type_id=et["id"], start_utc=now + timedelta(days=2))
    future = make_booking(event_type_id=et["id"], start_utc=now + timedelta(days=20))

    start = (now - timedelta(days=1)).isoformat()
    end = (now + timedelta(days=10)).isoformat()
    r = auth_client.get("/bookings", params={"from": start, "to": end})
    assert r.status_code == 200, r.text
    ids = {x["id"] for x in r.json()["items"]}
    assert in_range["id"] in ids
    assert past["id"] not in ids
    assert future["id"] not in ids


def test_list_sorted_by_updated_at_desc(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    now = datetime.now(UTC)
    old = make_booking(event_type_id=et["id"], updated_at=now - timedelta(hours=2))
    newest = make_booking(event_type_id=et["id"], updated_at=now)
    mid = make_booking(event_type_id=et["id"], updated_at=now - timedelta(hours=1))

    r = auth_client.get("/bookings")
    assert r.status_code == 200, r.text
    ids = [b["id"] for b in r.json()["items"]]
    assert ids == [newest["id"], mid["id"], old["id"]]


def test_list_pagination(auth_client: TestClient, make_event_type, make_booking) -> None:
    et = make_event_type(auth_client)
    now = datetime.now(UTC)
    ids = []
    for i in range(3):
        b = make_booking(
            event_type_id=et["id"],
            updated_at=now + timedelta(seconds=i),
        )
        ids.append(b["id"])

    page = auth_client.get("/bookings?limit=2")
    assert page.status_code == 200, page.text
    body = page.json()
    assert len(body["items"]) == 2
    assert body["nextCursor"] is not None

    page2 = auth_client.get(f"/bookings?limit=2&cursor={body['nextCursor']}")
    body2 = page2.json()
    assert len(body2["items"]) == 1
    assert body2["nextCursor"] is None

    seen = {b["id"] for b in body["items"]} | {b["id"] for b in body2["items"]}
    assert seen == set(ids)


def test_list_auto_cancel_sweep_stale(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    """pending/rescheduled whose startUtc has passed → cancelled on read."""
    et = make_event_type(auth_client)
    stale_pending = make_booking(
        event_type_id=et["id"],
        status="pending",
        start_utc=datetime.now(UTC) - timedelta(hours=1),
    )
    stale_rescheduled = make_booking(
        event_type_id=et["id"],
        status="rescheduled",
        start_utc=datetime.now(UTC) - timedelta(hours=2),
    )
    # Confirmed in the past stays as-is (history).
    past_confirmed = make_booking(
        event_type_id=et["id"],
        status="confirmed",
        start_utc=datetime.now(UTC) - timedelta(hours=3),
    )

    r = auth_client.get("/bookings")
    assert r.status_code == 200, r.text
    by_id = {b["id"]: b["status"] for b in r.json()["items"]}
    assert by_id[stale_pending["id"]] == "cancelled"
    assert by_id[stale_rescheduled["id"]] == "cancelled"
    assert by_id[past_confirmed["id"]] == "confirmed"


# ---------------------------------------------------------------------------
# B2 — GET /bookings/{id}
# ---------------------------------------------------------------------------


def test_read_requires_auth(client: TestClient) -> None:
    assert client.get("/bookings/abc").status_code == 401


def test_read_own_booking_200(auth_client: TestClient, make_event_type, make_booking) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"])
    r = auth_client.get(f"/bookings/{b['id']}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == b["id"]
    assert body["eventTypeId"] == et["id"]
    assert body["attendee"]["email"] == "alice@example.com"
    assert body["status"] == "pending"


def test_read_other_users_booking_404(
    auth_client: TestClient,
    other_user_client: TestClient,
    make_event_type,
    make_booking,
) -> None:
    et_other = make_event_type(other_user_client)
    theirs = make_booking(event_type_id=et_other["id"])
    r = auth_client.get(f"/bookings/{theirs['id']}")
    assert r.status_code == 404, r.text


def test_read_unknown_booking_404(auth_client: TestClient) -> None:
    r = auth_client.get("/bookings/does-not-exist")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# B3 — POST /bookings/{id}/cancel
# ---------------------------------------------------------------------------


def test_cancel_requires_auth(client: TestClient) -> None:
    assert client.post("/bookings/abc/cancel").status_code == 401


def test_cancel_pending_to_cancelled(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="pending")
    r = auth_client.post(f"/bookings/{b['id']}/cancel")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_confirmed_to_cancelled(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="confirmed")
    r = auth_client.post(f"/bookings/{b['id']}/cancel")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_rescheduled_to_cancelled(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="rescheduled")
    r = auth_client.post(f"/bookings/{b['id']}/cancel")
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_cancel_already_cancelled_409(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="cancelled")
    r = auth_client.post(f"/bookings/{b['id']}/cancel")
    assert r.status_code == 409, r.text


def test_cancel_other_users_booking_404(
    auth_client: TestClient,
    other_user_client: TestClient,
    make_event_type,
    make_booking,
) -> None:
    et_other = make_event_type(other_user_client)
    theirs = make_booking(event_type_id=et_other["id"])
    r = auth_client.post(f"/bookings/{theirs['id']}/cancel")
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# B4 — POST /bookings/{id}/reschedule (owner)
# ---------------------------------------------------------------------------


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def test_reschedule_requires_auth(client: TestClient) -> None:
    r = client.post(
        "/bookings/abc/reschedule",
        json={"startUtc": _iso(datetime.now(UTC) + timedelta(days=2))},
    )
    assert r.status_code == 401


def test_reschedule_pending_stays_pending(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="pending")
    new_start = datetime.now(UTC) + timedelta(days=3)
    r = auth_client.post(
        f"/bookings/{b['id']}/reschedule",
        json={"startUtc": _iso(new_start)},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "pending"
    assert body["startUtc"].startswith(new_start.replace(microsecond=0).isoformat()[:19])


def test_reschedule_confirmed_stays_confirmed(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="confirmed")
    new_start = datetime.now(UTC) + timedelta(days=3)
    r = auth_client.post(
        f"/bookings/{b['id']}/reschedule",
        json={"startUtc": _iso(new_start)},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "confirmed"


def test_reschedule_rescheduled_becomes_confirmed(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    """ADR-0001: owner-initiated reschedule collapses rescheduled → confirmed."""
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="rescheduled")
    new_start = datetime.now(UTC) + timedelta(days=3)
    r = auth_client.post(
        f"/bookings/{b['id']}/reschedule",
        json={"startUtc": _iso(new_start)},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "confirmed"


def test_reschedule_cancelled_409(auth_client: TestClient, make_event_type, make_booking) -> None:
    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="cancelled")
    r = auth_client.post(
        f"/bookings/{b['id']}/reschedule",
        json={"startUtc": _iso(datetime.now(UTC) + timedelta(days=3))},
    )
    assert r.status_code == 409, r.text


def test_reschedule_owner_does_not_rotate_manage_token(
    auth_client: TestClient, make_event_type, make_booking
) -> None:
    """ADR-0001: owner-side reschedule leaves manage_token unchanged.

    We can't read the token back through the API, but we verify the hash
    still verifies against the original token via the DB.
    """
    from app.auth.service import verify_password
    from app.db.models.booking import Booking as BookingModel
    from app.db.session import SessionLocal

    et = make_event_type(auth_client)
    b = make_booking(event_type_id=et["id"], status="confirmed", manage_token="secret-xyz")
    auth_client.post(
        f"/bookings/{b['id']}/reschedule",
        json={"startUtc": _iso(datetime.now(UTC) + timedelta(days=3))},
    )

    session = SessionLocal()
    try:
        row = session.get(BookingModel, b["id"])
        assert verify_password("secret-xyz", row.manage_token_hash)
    finally:
        session.close()


def test_reschedule_other_users_booking_404(
    auth_client: TestClient,
    other_user_client: TestClient,
    make_event_type,
    make_booking,
) -> None:
    et_other = make_event_type(other_user_client)
    theirs = make_booking(event_type_id=et_other["id"])
    r = auth_client.post(
        f"/bookings/{theirs['id']}/reschedule",
        json={"startUtc": _iso(datetime.now(UTC) + timedelta(days=3))},
    )
    assert r.status_code == 404, r.text
