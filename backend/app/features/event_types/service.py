"""EventTypes service — create, list, read, update, delete."""

from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.errors import BackendError
from app.core.pagination import DEFAULT_LIMIT, MAX_LIMIT
from app.db.models.event_type import EventType
from app.db.models.schedule import Schedule

_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _validate_color(color: str | None) -> None:
    if color is not None and not _COLOR_RE.match(color):
        raise BackendError(422, "invalid color", details=color)


def _validate_schedule_owned(session, user_id: str, schedule_id: str) -> Schedule:
    schedule = session.get(Schedule, schedule_id)
    if schedule is None or schedule.user_id != user_id:
        raise BackendError(409, "schedule not owned by user", details=schedule_id)
    return schedule


def create_event_type(
    session,
    user_id: str,
    *,
    slug: str,
    title: str,
    duration_min: int,
    location: str,
    schedule_id: str,
    description: str | None = None,
    color: str | None = None,
    padding_min_before: int | None = None,
    padding_min_after: int | None = None,
    min_notice_min: int | None = None,
    requires_confirmation: bool | None = None,
) -> dict:
    """Create an event type for the given user."""
    _validate_color(color)
    _validate_schedule_owned(session, user_id, schedule_id)

    et = EventType(
        user_id=user_id,
        schedule_id=schedule_id,
        slug=slug,
        title=title,
        description=description,
        duration_min=duration_min,
        location=location,
        color=color,
        padding_min_before=padding_min_before if padding_min_before is not None else 0,
        padding_min_after=padding_min_after if padding_min_after is not None else 0,
        min_notice_min=min_notice_min if min_notice_min is not None else 0,
        requires_confirmation=bool(requires_confirmation)
        if requires_confirmation is not None
        else False,
    )
    session.add(et)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise BackendError(409, "event type slug already in use", details=slug) from exc
    session.refresh(et)
    return _event_type_to_dict(et)


def list_event_types(
    session,
    user_id: str,
    *,
    schedule_id: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List the current user's event types, optionally filtered by scheduleId.

    Cursor is `<iso_created_at>::<id>` (created_at may collide between rows).
    """
    page_limit = min(limit or DEFAULT_LIMIT, MAX_LIMIT)

    stmt = select(EventType).where(EventType.user_id == user_id)
    if schedule_id is not None:
        stmt = stmt.where(EventType.schedule_id == schedule_id)
    if cursor:
        try:
            cur_iso, cur_id = cursor.split("::", 1)
            cur_dt = datetime.fromisoformat(cur_iso)
        except ValueError as exc:
            raise BackendError(400, "invalid cursor") from exc
        stmt = stmt.where(
            (EventType.created_at > cur_dt)
            | ((EventType.created_at == cur_dt) & (EventType.id > cur_id))
        )
    stmt = stmt.order_by(EventType.created_at, EventType.id).limit(page_limit + 1)

    rows = list(session.execute(stmt).scalars())
    has_more = len(rows) > page_limit
    items = rows[:page_limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last.created_at.isoformat()}::{last.id}"

    return {
        "items": [_event_type_to_dict(e) for e in items],
        "nextCursor": next_cursor,
    }


def get_event_type(session, user_id: str, event_type_id: str) -> dict:
    """Return an event type owned by `user_id`. 404 if missing or owned by someone else."""
    return _event_type_to_dict(_load_owned(session, user_id, event_type_id))


def update_event_type(
    session,
    user_id: str,
    event_type_id: str,
    *,
    slug: str | None = None,
    title: str | None = None,
    description: str | None = None,
    duration_min: int | None = None,
    location: str | None = None,
    color: str | None = None,
    schedule_id: str | None = None,
    padding_min_before: int | None = None,
    padding_min_after: int | None = None,
    min_notice_min: int | None = None,
    requires_confirmation: bool | None = None,
) -> dict:
    """Partial update of an event type."""
    et = _load_owned(session, user_id, event_type_id)

    new_color = color if color is not None else et.color
    _validate_color(new_color)
    if color is not None:
        # allow explicit null to clear
        et.color = color

    if schedule_id is not None:
        _validate_schedule_owned(session, user_id, schedule_id)
        et.schedule_id = schedule_id

    if slug is not None:
        et.slug = slug
    if title is not None:
        et.title = title
    if description is not None:
        et.description = description
    if duration_min is not None:
        et.duration_min = duration_min
    if location is not None:
        et.location = location
    if padding_min_before is not None:
        et.padding_min_before = padding_min_before
    if padding_min_after is not None:
        et.padding_min_after = padding_min_after
    if min_notice_min is not None:
        et.min_notice_min = min_notice_min
    if requires_confirmation is not None:
        et.requires_confirmation = bool(requires_confirmation)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise BackendError(409, "event type slug already in use", details=slug) from exc
    session.refresh(et)
    return _event_type_to_dict(et)


def delete_event_type(session, user_id: str, event_type_id: str) -> None:
    """Delete an event type.

    TODO (post-B): return 409 if a non-cancelled Booking still references it.
    """
    et = _load_owned(session, user_id, event_type_id)
    session.delete(et)
    session.commit()


def _load_owned(session, user_id: str, event_type_id: str) -> EventType:
    et = session.get(EventType, event_type_id)
    if et is None or et.user_id != user_id:
        raise BackendError(404, "event type not found")
    return et


def _event_type_to_dict(et: EventType) -> dict:
    return {
        "id": et.id,
        "slug": et.slug,
        "title": et.title,
        "description": et.description,
        "durationMin": et.duration_min,
        "location": et.location,
        "color": et.color,
        "scheduleId": et.schedule_id,
        "paddingMinBefore": et.padding_min_before,
        "paddingMinAfter": et.padding_min_after,
        "minNoticeMin": et.min_notice_min,
        "requiresConfirmation": et.requires_confirmation,
        "createdAt": et.created_at.isoformat(),
    }
