"""Schedules service — create, list, get, update, delete, overrides."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select

from app.core.errors import BackendError
from app.core.pagination import DEFAULT_LIMIT, MAX_LIMIT
from app.db.models.schedule import Schedule, ScheduleOverride, WorkingHours


def _validate_timezone(timezone: str) -> None:
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise BackendError(400, "unknown timezone", details=timezone) from exc


def create_schedule(
    session,
    user_id: str,
    *,
    name: str,
    timezone: str,
    working_hours: list[dict],
    overrides: list[dict] | None = None,
) -> dict:
    """Create a schedule and return it as a dict."""
    _validate_timezone(timezone)

    schedule = Schedule(user_id=user_id, name=name, timezone=timezone)
    session.add(schedule)
    session.flush()  # populate schedule.id

    for wh in working_hours:
        session.add(
            WorkingHours(
                schedule_id=schedule.id,
                day_of_week=wh["dayOfWeek"],
                start_min=wh["startMin"],
                end_min=wh["endMin"],
            )
        )

    for ov in overrides or []:
        session.add(
            ScheduleOverride(
                schedule_id=schedule.id,
                date=ov["date"],
                start_min=ov["startMin"],
                end_min=ov["endMin"],
                available=ov["available"],
            )
        )

    session.commit()
    session.refresh(schedule)
    return _schedule_to_dict(session, schedule)


def list_schedules(
    session,
    user_id: str,
    *,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List the current user's schedules, ordered by createdAt ASC.

    Cursor is `<iso_created_at>::<id>` (created_at may collide between rows).
    """
    page_limit = min(limit or DEFAULT_LIMIT, MAX_LIMIT)

    stmt = select(Schedule).where(Schedule.user_id == user_id)
    if cursor:
        try:
            cur_iso, cur_id = cursor.split("::", 1)
            cur_dt = datetime.fromisoformat(cur_iso)
        except ValueError as exc:
            raise BackendError(400, "invalid cursor") from exc
        stmt = stmt.where(
            (Schedule.created_at > cur_dt)
            | ((Schedule.created_at == cur_dt) & (Schedule.id > cur_id))
        )
    stmt = stmt.order_by(Schedule.created_at, Schedule.id).limit(page_limit + 1)

    rows = list(session.execute(stmt).scalars())
    has_more = len(rows) > page_limit
    items = rows[:page_limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last.created_at.isoformat()}::{last.id}"

    return {
        "items": [_schedule_to_dict(session, s) for s in items],
        "nextCursor": next_cursor,
    }


def get_schedule(session, user_id: str, schedule_id: str) -> dict:
    """Return a schedule owned by `user_id`. 404 if missing or owned by someone else."""
    schedule = session.get(Schedule, schedule_id)
    if schedule is None or schedule.user_id != user_id:
        raise BackendError(404, "schedule not found")
    return _schedule_to_dict(session, schedule)


def _load_owned(session, user_id: str, schedule_id: str) -> Schedule:
    """Return the Schedule ORM row, enforcing ownership (404 otherwise)."""
    schedule = session.get(Schedule, schedule_id)
    if schedule is None or schedule.user_id != user_id:
        raise BackendError(404, "schedule not found")
    return schedule


def update_schedule(
    session,
    user_id: str,
    schedule_id: str,
    *,
    name: str | None = None,
    timezone: str | None = None,
    working_hours: list[dict] | None = None,
) -> dict:
    """Partial update of a schedule.

    Per ADR-0002 changing `timezone` keeps WorkingHours.startMin/endMin as-is
    (wall-clock preservation). Passing `workingHours` replaces the set.
    """
    schedule = _load_owned(session, user_id, schedule_id)

    if timezone is not None:
        _validate_timezone(timezone)
        schedule.timezone = timezone
    if name is not None:
        schedule.name = name
    if working_hours is not None:
        session.query(WorkingHours).filter(WorkingHours.schedule_id == schedule.id).delete()
        for wh in working_hours:
            session.add(
                WorkingHours(
                    schedule_id=schedule.id,
                    day_of_week=wh["dayOfWeek"],
                    start_min=wh["startMin"],
                    end_min=wh["endMin"],
                )
            )

    session.commit()
    session.refresh(schedule)
    return _schedule_to_dict(session, schedule)


def delete_schedule(session, user_id: str, schedule_id: str) -> None:
    """Delete a schedule and its dependent rows.

    TODO (post-E): return 409 if any EventType still references this schedule.
    """
    schedule = _load_owned(session, user_id, schedule_id)
    session.delete(schedule)
    session.commit()


def _override_to_dict(ov: ScheduleOverride) -> dict:
    return {
        "date": ov.date,
        "startMin": ov.start_min,
        "endMin": ov.end_min,
        "available": ov.available,
    }


def add_override(session, user_id: str, schedule_id: str, *, override: dict) -> dict:
    """Upsert an override on the given date for the given schedule.

    `available=false` semantically blocks the whole day; the stored interval is
    kept verbatim (callers decide what it means for slot compilation later).
    """
    _load_owned(session, user_id, schedule_id)

    existing = (
        session.query(ScheduleOverride)
        .filter(
            ScheduleOverride.schedule_id == schedule_id,
            ScheduleOverride.date == override["date"],
        )
        .one_or_none()
    )
    if existing is None:
        row = ScheduleOverride(
            schedule_id=schedule_id,
            date=override["date"],
            start_min=override["startMin"],
            end_min=override["endMin"],
            available=override["available"],
        )
        session.add(row)
    else:
        existing.start_min = override["startMin"]
        existing.end_min = override["endMin"]
        existing.available = override["available"]
        row = existing

    session.commit()
    session.refresh(row)
    return _override_to_dict(row)


def list_overrides(session, user_id: str, schedule_id: str) -> list[dict]:
    """List overrides for a schedule, sorted by date."""
    _load_owned(session, user_id, schedule_id)
    rows = (
        session.query(ScheduleOverride)
        .filter(ScheduleOverride.schedule_id == schedule_id)
        .order_by(ScheduleOverride.date)
        .all()
    )
    return [_override_to_dict(r) for r in rows]


def remove_override(session, user_id: str, schedule_id: str, date: str) -> None:
    """Delete a single override by date. 404 if the date has no override."""
    _load_owned(session, user_id, schedule_id)
    row = (
        session.query(ScheduleOverride)
        .filter(
            ScheduleOverride.schedule_id == schedule_id,
            ScheduleOverride.date == date,
        )
        .one_or_none()
    )
    if row is None:
        raise BackendError(404, "override not found")
    session.delete(row)
    session.commit()


def _schedule_to_dict(session, schedule: Schedule) -> dict:
    """Serialize a schedule with its working hours and overrides."""
    working_hours = (
        session.query(WorkingHours)
        .filter(WorkingHours.schedule_id == schedule.id)
        .order_by(WorkingHours.day_of_week, WorkingHours.start_min)
        .all()
    )
    overrides = (
        session.query(ScheduleOverride)
        .filter(ScheduleOverride.schedule_id == schedule.id)
        .order_by(ScheduleOverride.date)
        .all()
    )
    return {
        "id": schedule.id,
        "name": schedule.name,
        "timezone": schedule.timezone,
        "workingHours": [
            {"dayOfWeek": wh.day_of_week, "startMin": wh.start_min, "endMin": wh.end_min}
            for wh in working_hours
        ],
        "overrides": [
            {
                "date": ov.date,
                "startMin": ov.start_min,
                "endMin": ov.end_min,
                "available": ov.available,
            }
            for ov in overrides
        ],
        "createdAt": schedule.created_at.isoformat(),
    }
