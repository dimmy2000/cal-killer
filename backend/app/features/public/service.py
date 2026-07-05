"""Public booking service — orchestration over slots + bookings + manage tokens."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import hash_password, verify_password
from app.core.errors import BackendError
from app.db.models.booking import Attendee, Booking
from app.db.models.event_type import EventType
from app.db.models.schedule import Schedule, ScheduleOverride, WorkingHours
from app.db.models.user import User
from app.features.public import slots as slots_mod

MAX_WINDOW_DAYS = 60
PAD_MIN = 0  # padding is not configured per-event in the tests; default 0


def _parse_dt(value: str, field: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BackendError(400, f"invalid {field}", details=value) from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _resolve_event(
    session: Session, owner_slug: str, event_slug: str
) -> tuple[User, EventType, Schedule]:
    user = session.query(User).filter(User.username == owner_slug).one_or_none()
    if user is None:
        raise BackendError(404, "event not found")
    et = (
        session.query(EventType)
        .filter(EventType.user_id == user.id, EventType.slug == event_slug)
        .one_or_none()
    )
    if et is None:
        raise BackendError(404, "event not found")
    schedule = session.get(Schedule, et.schedule_id)
    if schedule is None:
        raise BackendError(404, "event not found")
    return user, et, schedule


def get_public_event(session: Session, owner_slug: str, event_slug: str) -> dict:
    user, et, _ = _resolve_event(session, owner_slug, event_slug)
    return {
        "title": et.title,
        "description": et.description,
        "durationMin": et.duration_min,
        "location": et.location,
        "color": et.color,
        "ownerName": user.name,
        "ownerTimezone": user.timezone,
        "requiresConfirmation": et.requires_confirmation,
    }


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------


def _schedule_bookings(session: Session, schedule_id: str) -> list[dict]:
    """All bookings whose EventType references this Schedule (ADR-0004)."""
    stmt = (
        select(Booking)
        .join(EventType, Booking.event_type_id == EventType.id)
        .where(EventType.schedule_id == schedule_id, Booking.status != "cancelled")
    )
    rows = list(session.execute(stmt).scalars())
    return [{"startUtc": b.start_utc, "endUtc": b.end_utc} for b in rows]


def get_slots(
    session: Session,
    owner_slug: str,
    event_slug: str,
    *,
    from_str: str,
    to_str: str,
) -> list[dict]:
    _, et, schedule = _resolve_event(session, owner_slug, event_slug)
    from_utc = _parse_dt(from_str, "from")
    to_utc = _parse_dt(to_str, "to")
    if to_utc <= from_utc:
        raise BackendError(400, "invalid range")
    if (to_utc - from_utc).days > MAX_WINDOW_DAYS:
        raise BackendError(400, "range too wide")

    working_hours = (
        session.query(WorkingHours).filter(WorkingHours.schedule_id == schedule.id).all()
    )
    overrides = (
        session.query(ScheduleOverride).filter(ScheduleOverride.schedule_id == schedule.id).all()
    )
    bookings = _schedule_bookings(session, schedule.id)

    return slots_mod.compile_slots(
        working_hours=[
            {"dayOfWeek": w.day_of_week, "startMin": w.start_min, "endMin": w.end_min}
            for w in working_hours
        ],
        overrides=[
            {
                "date": o.date,
                "startMin": o.start_min,
                "endMin": o.end_min,
                "available": o.available,
            }
            for o in overrides
        ],
        bookings=bookings,
        duration_min=et.duration_min,
        min_notice_min=et.min_notice_min,
        tz_name=schedule.timezone,
        from_utc=from_utc,
        to_utc=to_utc,
        now=datetime.now(UTC),
    )


# ---------------------------------------------------------------------------
# Booking creation
# ---------------------------------------------------------------------------


def _new_token() -> str:
    return secrets.token_urlsafe(24)


def _iso(dt: datetime) -> str:
    """Serialize a datetime to ISO-8601 UTC with a trailing Z.

    SQLite strips tzinfo on read-back, so naive datetimes are re-stamped UTC.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _booking_to_dict(booking: Booking, attendee: Attendee) -> dict:
    return {
        "id": booking.id,
        "status": booking.status,
        "startUtc": _iso(booking.start_utc),
        "endUtc": _iso(booking.end_utc),
        "eventTypeId": booking.event_type_id,
        "attendee": {
            "name": attendee.name,
            "email": attendee.email,
            "notes": attendee.notes,
            "timezone": attendee.timezone,
        },
        "location": booking.location,
        "createdAt": _iso(booking.created_at),
        "updatedAt": _iso(booking.updated_at),
    }


def _validate_slot(
    session: Session,
    et: EventType,
    schedule: Schedule,
    start_utc: datetime,
) -> None:
    """Grid alignment + min notice + conflict checks."""
    now = datetime.now(UTC)
    if start_utc < now + timedelta(minutes=et.min_notice_min):
        raise BackendError(400, "start is too soon (minNotice)")

    # Grid alignment: convert to local and check offset from the matching
    # WorkingHours.startMin (ADR-0004). (startMin - midnight) % duration == 0.
    from zoneinfo import ZoneInfo

    local = start_utc.astimezone(ZoneInfo(schedule.timezone))
    local_min = local.hour * 60 + local.minute
    whs = session.query(WorkingHours).filter(WorkingHours.day_of_week == local.weekday() + 1).all()
    aligned = False
    for wh in whs:
        if (
            wh.start_min <= local_min < wh.end_min
            and et.duration_min > 0
            and (local_min - wh.start_min) % et.duration_min == 0
        ):
            aligned = True
            break
    if not aligned:
        raise BackendError(400, "start is not grid-aligned")

    end_utc = start_utc + timedelta(minutes=et.duration_min)
    conflicts = _schedule_bookings(session, schedule.id)
    for c in conflicts:
        cs = _as_utc_dt(c["startUtc"])
        ce = _as_utc_dt(c["endUtc"])
        if start_utc < ce and cs < end_utc:
            raise BackendError(409, "slot is already booked")


def _as_utc_dt(value) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return _parse_dt(value, "startUtc")


def create_booking(
    session: Session,
    owner_slug: str,
    event_slug: str,
    *,
    attendee: dict,
    start_utc_str: str,
) -> dict:
    _, et, schedule = _resolve_event(session, owner_slug, event_slug)
    start_utc = _parse_dt(start_utc_str, "startUtc")
    _validate_slot(session, et, schedule, start_utc)

    end_utc = start_utc + timedelta(minutes=et.duration_min)
    status = "pending" if et.requires_confirmation else "confirmed"
    token = _new_token()

    att = Attendee(
        name=attendee["name"],
        email=attendee["email"],
        notes=attendee.get("notes"),
        timezone=attendee["timezone"],
    )
    session.add(att)
    session.flush()

    now = datetime.now(UTC)
    booking = Booking(
        event_type_id=et.id,
        status=status,
        start_utc=start_utc,
        end_utc=end_utc,
        location=et.location,
        manage_token_hash=hash_password(token),
        attendee_id=att.id,
        created_at=now,
        updated_at=now,
    )
    session.add(booking)
    session.commit()
    session.refresh(booking)
    session.refresh(att)
    return {"booking": _booking_to_dict(booking, att), "manageToken": token}


# ---------------------------------------------------------------------------
# Manage-token gated operations
# ---------------------------------------------------------------------------


def _load_booking_by_token(
    session: Session, booking_id: str, token: str
) -> tuple[Booking, Attendee]:
    booking = session.get(Booking, booking_id)
    if booking is None:
        raise BackendError(404, "booking not found")
    if not verify_password(token, booking.manage_token_hash):
        raise BackendError(401, "invalid manage token")
    attendee = session.get(Attendee, booking.attendee_id)
    return booking, attendee


def get_public_booking(session: Session, booking_id: str, token: str) -> dict:
    booking, attendee = _load_booking_by_token(session, booking_id, token)
    return _booking_to_dict(booking, attendee)


def confirm_booking(session: Session, booking_id: str, token: str) -> dict:
    booking, attendee = _load_booking_by_token(session, booking_id, token)
    if booking.status == "cancelled":
        raise BackendError(409, "booking is cancelled")
    booking.status = "confirmed"
    booking.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(booking)
    return _booking_to_dict(booking, attendee)


def cancel_public_booking(session: Session, booking_id: str, token: str) -> dict:
    booking, attendee = _load_booking_by_token(session, booking_id, token)
    if booking.status == "cancelled":
        raise BackendError(409, "booking already cancelled")
    booking.status = "cancelled"
    booking.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(booking)
    return _booking_to_dict(booking, attendee)


def reschedule_public_booking(
    session: Session,
    booking_id: str,
    token: str,
    start_utc_str: str,
) -> dict:
    booking, attendee = _load_booking_by_token(session, booking_id, token)
    if booking.status == "cancelled":
        raise BackendError(409, "cannot reschedule a cancelled booking")

    et = session.get(EventType, booking.event_type_id)
    schedule = session.get(Schedule, et.schedule_id)
    new_start = _parse_dt(start_utc_str, "startUtc")
    _validate_slot(session, et, schedule, new_start)

    duration = booking.end_utc - booking.start_utc
    booking.start_utc = new_start
    booking.end_utc = new_start + duration
    booking.updated_at = datetime.now(UTC)

    # Rotate token on attendee-reschedule.
    new_token = _new_token()
    booking.manage_token_hash = hash_password(new_token)

    # Status (ADR-0001): pending→rescheduled, confirmed→rescheduled,
    # rescheduled stays. (Auto-confirm is an owner action; the public
    # reschedule leaves it in `rescheduled`.)
    if booking.status != "rescheduled":
        booking.status = "rescheduled"

    session.commit()
    session.refresh(booking)
    session.refresh(attendee)
    return {"booking": _booking_to_dict(booking, attendee), "manageToken": new_token}
