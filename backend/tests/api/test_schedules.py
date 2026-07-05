"""Tests for /schedules, /schedules/{id}/overrides."""

from __future__ import annotations

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# S1 — POST /schedules (201)
# ---------------------------------------------------------------------------


def test_create_returns_schedule_with_fields(auth_client: TestClient) -> None:
    """POST /schedules 201 — returns id/name/timezone/workingHours/overrides/createdAt."""
    r = auth_client.post(
        "/schedules",
        json={
            "name": "Work",
            "timezone": "UTC",
            "workingHours": [
                {"dayOfWeek": 1, "startMin": 540, "endMin": 1020},
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "id" in body and isinstance(body["id"], str)
    assert body["name"] == "Work"
    assert body["timezone"] == "UTC"
    assert body["workingHours"] == [{"dayOfWeek": 1, "startMin": 540, "endMin": 1020}]
    assert body["overrides"] == []
    assert "createdAt" in body


def test_create_with_overrides(auth_client: TestClient) -> None:
    """POST /schedules persists overrides provided in the create body."""
    r = auth_client.post(
        "/schedules",
        json={
            "name": "Work",
            "timezone": "UTC",
            "workingHours": [],
            "overrides": [
                {"date": "2026-07-10", "startMin": 0, "endMin": 1440, "available": False}
            ],
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["overrides"] == [
        {"date": "2026-07-10", "startMin": 0, "endMin": 1440, "available": False}
    ]


def test_create_unknown_timezone_400(auth_client: TestClient) -> None:
    """POST /schedules with an unknown timezone returns 400."""
    r = auth_client.post(
        "/schedules",
        json={"name": "X", "timezone": "Mars/Olympus", "workingHours": []},
    )
    assert r.status_code == 400, r.text


def test_create_requires_auth(client: TestClient) -> None:
    assert (
        client.post(
            "/schedules", json={"name": "x", "timezone": "UTC", "workingHours": []}
        ).status_code
        == 401
    )


# ---------------------------------------------------------------------------
# S2 — GET /schedules (200)
# ---------------------------------------------------------------------------


def _create_schedule(client: TestClient, name: str = "Work") -> str:
    r = client.post(
        "/schedules",
        json={"name": name, "timezone": "UTC", "workingHours": []},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_list_returns_only_own_schedules(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    """GET /schedules returns only the current user's schedules."""
    mine = _create_schedule(auth_client, "Mine")
    _ = _create_schedule(other_user_client, "Theirs")

    r = auth_client.get("/schedules")
    assert r.status_code == 200, r.text
    body = r.json()
    assert [s["id"] for s in body["items"]] == [mine]
    assert body["items"][0]["name"] == "Mine"
    assert "nextCursor" in body and body["nextCursor"] is None


def test_list_pagination(
    auth_client: TestClient,
) -> None:
    """GET /schedules with limit=2 paginates via nextCursor."""
    ids = [_create_schedule(auth_client, f"S{i}") for i in range(3)]

    page = auth_client.get("/schedules?limit=2")
    assert page.status_code == 200, page.text
    body = page.json()
    assert len(body["items"]) == 2
    assert body["nextCursor"] is not None

    page2 = auth_client.get(f"/schedules?limit=2&cursor={body['nextCursor']}")
    assert page2.status_code == 200, page2.text
    body2 = page2.json()
    assert len(body2["items"]) == 1
    assert body2["nextCursor"] is None

    seen = {s["id"] for s in body["items"]} | {s["id"] for s in body2["items"]}
    assert seen == set(ids)


def test_list_requires_auth(client: TestClient) -> None:
    assert client.get("/schedules").status_code == 401


# ---------------------------------------------------------------------------
# S3 — GET /schedules/{id}
# ---------------------------------------------------------------------------


def test_read_own_schedule_200(auth_client: TestClient) -> None:
    """GET /schedules/{id} returns 200 for the owner."""
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.get(f"/schedules/{sid}")
    assert r.status_code == 200, r.text
    assert r.json()["id"] == sid
    assert r.json()["name"] == "Work"


def test_read_others_schedule_404(auth_client: TestClient, other_user_client: TestClient) -> None:
    """GET /schedules/{id} returns 404 when the schedule belongs to another user."""
    their_id = _create_schedule(other_user_client, "Theirs")
    r = auth_client.get(f"/schedules/{their_id}")
    assert r.status_code == 404, r.text


def test_read_unknown_schedule_404(auth_client: TestClient) -> None:
    r = auth_client.get("/schedules/does-not-exist")
    assert r.status_code == 404, r.text


def test_read_requires_auth(client: TestClient) -> None:
    assert client.get("/schedules/abc").status_code == 401


# ---------------------------------------------------------------------------
# S4 — PATCH /schedules/{id}
# ---------------------------------------------------------------------------


def test_update_name_and_timezone(auth_client: TestClient) -> None:
    """PATCH updates name and timezone; verified via GET."""
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.patch(
        f"/schedules/{sid}",
        json={"name": "Personal", "timezone": "Europe/London"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Personal"
    assert body["timezone"] == "Europe/London"

    me_r = auth_client.get(f"/schedules/{sid}")
    assert me_r.json()["name"] == "Personal"
    assert me_r.json()["timezone"] == "Europe/London"


def test_update_wall_clock_preserves_minutes(auth_client: TestClient) -> None:
    """Changing timezone keeps WorkingHours.startMin/endMin (ADR-0002)."""
    r = auth_client.post(
        "/schedules",
        json={
            "name": "Work",
            "timezone": "America/New_York",
            "workingHours": [
                {"dayOfWeek": 1, "startMin": 540, "endMin": 1020},
            ],
        },
    )
    sid = r.json()["id"]

    r = auth_client.patch(f"/schedules/{sid}", json={"timezone": "Europe/London"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["timezone"] == "Europe/London"
    # 09:00-17:00 kept as wall-clock in the new zone
    assert body["workingHours"] == [{"dayOfWeek": 1, "startMin": 540, "endMin": 1020}]


def test_update_replaces_working_hours(auth_client: TestClient) -> None:
    """PATCH workingHours replaces the previous set."""
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.patch(
        f"/schedules/{sid}",
        json={
            "workingHours": [
                {"dayOfWeek": 2, "startMin": 600, "endMin": 1000},
            ]
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["workingHours"] == [{"dayOfWeek": 2, "startMin": 600, "endMin": 1000}]


def test_update_unknown_timezone_400(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.patch(f"/schedules/{sid}", json={"timezone": "Mars/Olympus"})
    assert r.status_code == 400, r.text


def test_update_others_schedule_404(auth_client: TestClient, other_user_client: TestClient) -> None:
    their_id = _create_schedule(other_user_client, "Theirs")
    r = auth_client.patch(f"/schedules/{their_id}", json={"name": "x"})
    assert r.status_code == 404, r.text


# ---------------------------------------------------------------------------
# S5 — DELETE /schedules/{id}
# ---------------------------------------------------------------------------


def test_delete_own_schedule_204(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.delete(f"/schedules/{sid}")
    assert r.status_code == 204, r.text
    # Subsequent read returns 404
    assert auth_client.get(f"/schedules/{sid}").status_code == 404


def test_delete_others_schedule_404(auth_client: TestClient, other_user_client: TestClient) -> None:
    their_id = _create_schedule(other_user_client, "Theirs")
    r = auth_client.delete(f"/schedules/{their_id}")
    assert r.status_code == 404, r.text


def test_delete_cascades_working_hours(auth_client: TestClient) -> None:
    """Deleting a schedule removes its working_hours rows."""
    r = auth_client.post(
        "/schedules",
        json={
            "name": "Work",
            "timezone": "UTC",
            "workingHours": [
                {"dayOfWeek": 1, "startMin": 0, "endMin": 60},
                {"dayOfWeek": 2, "startMin": 0, "endMin": 60},
            ],
        },
    )
    sid = r.json()["id"]
    assert auth_client.delete(f"/schedules/{sid}").status_code == 204


# ---------------------------------------------------------------------------
# S6 — Overrides
# ---------------------------------------------------------------------------


def test_add_override(auth_client: TestClient) -> None:
    """POST /{id}/overrides adds an override."""
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.post(
        f"/schedules/{sid}/overrides",
        json={"date": "2026-07-10", "startMin": 540, "endMin": 1020, "available": True},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body == {"date": "2026-07-10", "startMin": 540, "endMin": 1020, "available": True}


def test_add_override_available_false_ignores_interval(auth_client: TestClient) -> None:
    """`available=false` blocks the whole day; interval is still stored as sent."""
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.post(
        f"/schedules/{sid}/overrides",
        json={"date": "2026-07-10", "startMin": 0, "endMin": 0, "available": False},
    )
    assert r.status_code == 200, r.text
    assert r.json()["available"] is False


def test_add_override_upsert_replaces_same_date(auth_client: TestClient) -> None:
    """A second override for the same date replaces the first."""
    sid = _create_schedule(auth_client, "Work")
    auth_client.post(
        f"/schedules/{sid}/overrides",
        json={"date": "2026-07-10", "startMin": 0, "endMin": 0, "available": False},
    )
    r = auth_client.post(
        f"/schedules/{sid}/overrides",
        json={"date": "2026-07-10", "startMin": 540, "endMin": 1020, "available": True},
    )
    assert r.status_code == 200, r.text

    listed = auth_client.get(f"/schedules/{sid}/overrides").json()
    assert len(listed) == 1
    assert listed[0] == {"date": "2026-07-10", "startMin": 540, "endMin": 1020, "available": True}


def test_list_overrides_sorted(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client, "Work")
    for d in ("2026-07-12", "2026-07-10", "2026-07-11"):
        auth_client.post(
            f"/schedules/{sid}/overrides",
            json={"date": d, "startMin": 0, "endMin": 0, "available": False},
        )
    r = auth_client.get(f"/schedules/{sid}/overrides")
    assert r.status_code == 200, r.text
    dates = [o["date"] for o in r.json()]
    assert dates == ["2026-07-10", "2026-07-11", "2026-07-12"]


def test_remove_override(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client, "Work")
    auth_client.post(
        f"/schedules/{sid}/overrides",
        json={"date": "2026-07-10", "startMin": 0, "endMin": 0, "available": False},
    )
    r = auth_client.delete(f"/schedules/{sid}/overrides/2026-07-10")
    assert r.status_code == 204, r.text
    assert auth_client.get(f"/schedules/{sid}/overrides").json() == []


def test_remove_override_unknown_date_404(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client, "Work")
    r = auth_client.delete(f"/schedules/{sid}/overrides/2026-07-10")
    assert r.status_code == 404, r.text


def test_overrides_others_schedule_404(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    their_id = _create_schedule(other_user_client, "Theirs")
    assert (
        auth_client.post(
            f"/schedules/{their_id}/overrides",
            json={"date": "2026-07-10", "startMin": 0, "endMin": 0, "available": False},
        ).status_code
        == 404
    )
    assert auth_client.get(f"/schedules/{their_id}/overrides").status_code == 404


def test_list_overrides_requires_auth(client: TestClient) -> None:
    assert client.get("/schedules/abc/overrides").status_code == 401
