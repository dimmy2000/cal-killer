"""Tests for /event-types."""

from __future__ import annotations

from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_schedule(client: TestClient, name: str = "Work") -> str:
    r = client.post(
        "/schedules",
        json={"name": name, "timezone": "UTC", "workingHours": []},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_event_type(
    client: TestClient,
    *,
    schedule_id: str,
    slug: str = "intro",
    title: str = "Intro Call",
    **overrides,
) -> dict:
    body = {
        "slug": slug,
        "title": title,
        "durationMin": 30,
        "location": "online",
        "scheduleId": schedule_id,
    }
    body.update(overrides)
    r = client.post("/event-types", json=body)
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# E1 — POST /event-types (201)
# ---------------------------------------------------------------------------


def test_create_returns_event_type_with_defaults(auth_client: TestClient) -> None:
    """POST /event-types 201 — applies defaults padding=0, minNotice=0, requiresConfirmation=false."""
    sid = _create_schedule(auth_client)
    body = _create_event_type(auth_client, schedule_id=sid)
    assert body["slug"] == "intro"
    assert body["title"] == "Intro Call"
    assert body["durationMin"] == 30
    assert body["location"] == "online"
    assert body["scheduleId"] == sid
    assert body["paddingMinBefore"] == 0
    assert body["paddingMinAfter"] == 0
    assert body["minNoticeMin"] == 0
    assert body["requiresConfirmation"] is False
    assert body["color"] is None
    assert body["description"] is None
    assert "id" in body and isinstance(body["id"], str)
    assert "createdAt" in body


def test_create_with_all_fields(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    body = _create_event_type(
        auth_client,
        schedule_id=sid,
        description="A 45-min deep dive",
        color="#A1B2C3",
        paddingMinBefore=10,
        paddingMinAfter=15,
        minNoticeMin=120,
        requiresConfirmation=True,
        durationMin=45,
        location="in_person",
    )
    assert body["description"] == "A 45-min deep dive"
    assert body["color"] == "#A1B2C3"
    assert body["paddingMinBefore"] == 10
    assert body["paddingMinAfter"] == 15
    assert body["minNoticeMin"] == 120
    assert body["requiresConfirmation"] is True
    assert body["durationMin"] == 45
    assert body["location"] == "in_person"


def test_create_duplicate_slug_same_user_409(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    _create_event_type(auth_client, schedule_id=sid, slug="intro")
    r = auth_client.post(
        "/event-types",
        json={
            "slug": "intro",
            "title": "Another",
            "durationMin": 30,
            "location": "online",
            "scheduleId": sid,
        },
    )
    assert r.status_code == 409, r.text


def test_create_same_slug_different_users_ok(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    """The same slug is allowed for different users."""
    sid_a = _create_schedule(auth_client)
    sid_b = _create_schedule(other_user_client)
    _create_event_type(auth_client, schedule_id=sid_a, slug="shared")
    body = _create_event_type(other_user_client, schedule_id=sid_b, slug="shared")
    assert body["slug"] == "shared"


def test_create_invalid_color_422(auth_client: TestClient) -> None:
    """color must match ^#[0-9A-Fa-f]{6}$."""
    sid = _create_schedule(auth_client)
    r = auth_client.post(
        "/event-types",
        json={
            "slug": "intro",
            "title": "Intro",
            "durationMin": 30,
            "location": "online",
            "scheduleId": sid,
            "color": "red",
        },
    )
    assert r.status_code == 422, r.text


def test_create_schedule_not_owned_409(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    """scheduleId belonging to another user → 409."""
    their_sid = _create_schedule(other_user_client)
    r = auth_client.post(
        "/event-types",
        json={
            "slug": "intro",
            "title": "Intro",
            "durationMin": 30,
            "location": "online",
            "scheduleId": their_sid,
        },
    )
    assert r.status_code == 409, r.text


def test_create_unknown_schedule_409(auth_client: TestClient) -> None:
    r = auth_client.post(
        "/event-types",
        json={
            "slug": "intro",
            "title": "Intro",
            "durationMin": 30,
            "location": "online",
            "scheduleId": "nonexistent-id",
        },
    )
    assert r.status_code == 409, r.text


def test_create_requires_auth(client: TestClient) -> None:
    assert (
        client.post(
            "/event-types",
            json={
                "slug": "x",
                "title": "x",
                "durationMin": 30,
                "location": "online",
                "scheduleId": "any",
            },
        ).status_code
        == 401
    )


# ---------------------------------------------------------------------------
# E2 — GET /event-types (200)
# ---------------------------------------------------------------------------


def test_list_returns_only_own_event_types(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    sid_a = _create_schedule(auth_client)
    sid_b = _create_schedule(other_user_client)
    mine = _create_event_type(auth_client, schedule_id=sid_a, slug="a")["id"]
    _create_event_type(other_user_client, schedule_id=sid_b, slug="b")

    r = auth_client.get("/event-types")
    assert r.status_code == 200, r.text
    body = r.json()
    assert [e["id"] for e in body["items"]] == [mine]
    assert body["nextCursor"] is None


def test_list_filter_by_schedule_id(auth_client: TestClient) -> None:
    sid1 = _create_schedule(auth_client, "One")
    sid2 = _create_schedule(auth_client, "Two")
    e1 = _create_event_type(auth_client, schedule_id=sid1, slug="a")["id"]
    e2 = _create_event_type(auth_client, schedule_id=sid2, slug="b")["id"]

    r = auth_client.get(f"/event-types?scheduleId={sid1}")
    assert r.status_code == 200, r.text
    ids = [e["id"] for e in r.json()["items"]]
    assert ids == [e1]
    assert e2 not in ids


def test_list_pagination(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    ids = [_create_event_type(auth_client, schedule_id=sid, slug=f"s{i}")["id"] for i in range(3)]

    page = auth_client.get("/event-types?limit=2")
    assert page.status_code == 200, page.text
    body = page.json()
    assert len(body["items"]) == 2
    assert body["nextCursor"] is not None

    page2 = auth_client.get(f"/event-types?limit=2&cursor={body['nextCursor']}")
    body2 = page2.json()
    assert len(body2["items"]) == 1
    assert body2["nextCursor"] is None

    seen = {e["id"] for e in body["items"]} | {e["id"] for e in body2["items"]}
    assert seen == set(ids)


def test_list_requires_auth(client: TestClient) -> None:
    assert client.get("/event-types").status_code == 401


# ---------------------------------------------------------------------------
# E3 — GET / PATCH / DELETE
# ---------------------------------------------------------------------------


def test_read_own_event_type_200(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    et = _create_event_type(auth_client, schedule_id=sid)
    r = auth_client.get(f"/event-types/{et['id']}")
    assert r.status_code == 200, r.text
    assert r.json()["id"] == et["id"]


def test_read_others_event_type_404(auth_client: TestClient, other_user_client: TestClient) -> None:
    sid_b = _create_schedule(other_user_client)
    their_et = _create_event_type(other_user_client, schedule_id=sid_b)
    r = auth_client.get(f"/event-types/{their_et['id']}")
    assert r.status_code == 404, r.text


def test_read_unknown_event_type_404(auth_client: TestClient) -> None:
    r = auth_client.get("/event-types/does-not-exist")
    assert r.status_code == 404, r.text


def test_read_requires_auth(client: TestClient) -> None:
    assert client.get("/event-types/abc").status_code == 401


def test_patch_updates_fields(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    et = _create_event_type(auth_client, schedule_id=sid)
    r = auth_client.patch(
        f"/event-types/{et['id']}",
        json={"title": "Renamed", "durationMin": 60, "color": "#FF0000"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["title"] == "Renamed"
    assert body["durationMin"] == 60
    assert body["color"] == "#FF0000"


def test_patch_slug_rename_unique_kept(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    _create_event_type(auth_client, schedule_id=sid, slug="first")
    et2 = _create_event_type(auth_client, schedule_id=sid, slug="second")
    # rename et2 → "first" collides → 409
    r = auth_client.patch(f"/event-types/{et2['id']}", json={"slug": "first"})
    assert r.status_code == 409, r.text
    # rename et2 → "third" ok
    r2 = auth_client.patch(f"/event-types/{et2['id']}", json={"slug": "third"})
    assert r2.status_code == 200, r2.text
    assert r2.json()["slug"] == "third"


def test_patch_invalid_color_422(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    et = _create_event_type(auth_client, schedule_id=sid)
    r = auth_client.patch(f"/event-types/{et['id']}", json={"color": "#XYZ"})
    assert r.status_code == 422, r.text


def test_patch_schedule_id_not_owned_409(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    sid_a = _create_schedule(auth_client)
    sid_b = _create_schedule(other_user_client)
    et = _create_event_type(auth_client, schedule_id=sid_a)
    r = auth_client.patch(f"/event-types/{et['id']}", json={"scheduleId": sid_b})
    assert r.status_code == 409, r.text


def test_patch_others_event_type_404(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    sid_b = _create_schedule(other_user_client)
    their_et = _create_event_type(other_user_client, schedule_id=sid_b)
    r = auth_client.patch(f"/event-types/{their_et['id']}", json={"title": "x"})
    assert r.status_code == 404, r.text


def test_delete_own_event_type_204(auth_client: TestClient) -> None:
    sid = _create_schedule(auth_client)
    et = _create_event_type(auth_client, schedule_id=sid)
    r = auth_client.delete(f"/event-types/{et['id']}")
    assert r.status_code == 204, r.text
    assert auth_client.get(f"/event-types/{et['id']}").status_code == 404


def test_delete_others_event_type_404(
    auth_client: TestClient, other_user_client: TestClient
) -> None:
    sid_b = _create_schedule(other_user_client)
    their_et = _create_event_type(other_user_client, schedule_id=sid_b)
    r = auth_client.delete(f"/event-types/{their_et['id']}")
    assert r.status_code == 404, r.text


def test_delete_requires_auth(client: TestClient) -> None:
    assert client.delete("/event-types/abc").status_code == 401
