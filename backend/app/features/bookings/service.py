"""Bookings service — list / read / cancel / reschedule (owner-side)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BackendError
from app.core.pagination import DEFAULT_LIMIT, MAX_LIMIT
from app.db.models.booking import Attendee, Booking
from app.db.models.event_type import EventType

SWEEPABLE_STATUSES = ("pending", "rescheduled")


def _parse_dt(value: str, field: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BackendError(400, f"invalid {field}", details=value) from exc


def _as_utc(dt: datetime) -> datetime:
    """Normalize a datetime to UTC-aware (SQLite strips tzinfo on read-back)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _load_owned_booking(session: Session, user_id: str, booking_id: str) -> Booking:
    """Load a Booking belonging to `user_id` via its EventType.

    Returns 404 if the booking does not exist or is owned by another user.
    """
    stmt = (
        select(Booking)
        .join(EventType, Booking.event_type_id == EventType.id)
        .where(Booking.id == booking_id, EventType.user_id == user_id)
    )
    booking = session.execute(stmt).scalar_one_or_none()
    if booking is None:
        raise BackendError(404, "booking not found")
    return booking


def _sweep(session: Session, bookings: list[Booking]) -> None:
    """Lazy auto-cancel sweep (ADR-0005).

    `pending` / `rescheduled` Bookings whose startUtc has passed → `cancelled`.
    Mutates rows in-place and commits once if any transition occurred.
    """
    now = datetime.now(UTC)
    changed = False
    for b in bookings:
        if b.status in SWEEPABLE_STATUSES and _as_utc(b.start_utc) <= now:
            b.status = "cancelled"
            b.updated_at = now
            changed = True
    if changed:
        session.commit()


def list_bookings(
    session: Session,
    user_id: str,
    *,
    status: str | None = None,
    event_type_id: str | None = None,
    attendee_email: str | None = None,
    from_: datetime | None = None,
    to: datetime | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict:
    """List the current user's bookings, filtered and sorted by updatedAt DESC.

    Cursor is `<iso_updated_at>::<id>` (updated_at may collide between rows);
    because sort is DESC, the cursor predicate is the dual: rows strictly newer
    OR (equal timestamp with smaller id).
    """
    page_limit = min(limit or DEFAULT_LIMIT, MAX_LIMIT)

    stmt = (
        select(Booking)
        .join(EventType, Booking.event_type_id == EventType.id)
        .where(EventType.user_id == user_id)
    )
    if status is not None:
        stmt = stmt.where(Booking.status == status)
    if event_type_id is not None:
        stmt = stmt.where(Booking.event_type_id == event_type_id)
    if attendee_email is not None:
        stmt = stmt.join(Attendee, Booking.attendee_id == Attendee.id).where(
            Attendee.email == attendee_email
        )
    if from_ is not None:
        stmt = stmt.where(Booking.start_utc >= from_.replace(tzinfo=None))
    if to is not None:
        stmt = stmt.where(Booking.start_utc <= to.replace(tzinfo=None))
    if cursor:
        try:
            cur_iso, cur_id = cursor.split("::", 1)
            cur_dt = datetime.fromisoformat(cur_iso)
        except ValueError as exc:
            raise BackendError(400, "invalid cursor") from exc
        cur_dt_naive = cur_dt.replace(tzinfo=None)
        stmt = stmt.where(
            (Booking.updated_at < cur_dt_naive)
            | ((Booking.updated_at == cur_dt_naive) & (Booking.id < cur_id))
        )
    stmt = stmt.order_by(Booking.updated_at.desc(), Booking.id.desc()).limit(page_limit + 1)

    rows = list(session.execute(stmt).scalars())

    # Lazy sweep applies to rows that would be visible, then re-filter so a
    # status filter that excluded the swept rows pre-sweep still wins.
    _sweep(session, rows)
    if status is not None:
        rows = [b for b in rows if b.status == status]

    has_more = len(rows) > page_limit
    items = rows[:page_limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        next_cursor = f"{last.updated_at.isoformat()}::{last.id}"

    return {
        "items": [_booking_to_dict(session, b) for b in items],
        "nextCursor": next_cursor,
    }


def get_booking(session: Session, user_id: str, booking_id: str) -> dict:
    booking = _load_owned_booking(session, user_id, booking_id)
    # Lazy sweep also applies to single reads.
    _sweep(session, [booking])
    session.refresh(booking)
    return _booking_to_dict(session, booking)


def cancel_booking(session: Session, user_id: str, booking_id: str) -> dict:
    booking = _load_owned_booking(session, user_id, booking_id)
    # Lazy sweep first so an already-stale booking reflects cancelled status.
    _sweep(session, [booking])
    session.refresh(booking)
    if booking.status == "cancelled":
        raise BackendError(409, "booking already cancelled")
    booking.status = "cancelled"
    booking.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(booking)
    return _booking_to_dict(session, booking)


def reschedule_booking_owner(
    session: Session, user_id: str, booking_id: str, *, start_utc: str
) -> dict:
    booking = _load_owned_booking(session, user_id, booking_id)
    _sweep(session, [booking])
    session.refresh(booking)
    if booking.status == "cancelled":
        raise BackendError(409, "cannot reschedule a cancelled booking")

    new_start = _parse_dt(start_utc, "startUtc")
    duration = booking.end_utc - booking.start_utc
    booking.start_utc = new_start
    booking.end_utc = new_start + duration
    booking.updated_at = datetime.now(UTC)

    # Owner-initiated post-reschedule status (ADR-0001):
    #   pending → pending
    #   confirmed → confirmed
    #   rescheduled → confirmed
    if booking.status == "rescheduled":
        booking.status = "confirmed"

    session.commit()
    session.refresh(booking)
    return _booking_to_dict(session, booking)


def _booking_to_dict(session: Session, booking: Booking) -> dict:
    attendee = session.get(Attendee, booking.attendee_id)
    return {
        "id": booking.id,
        "status": booking.status,
        "startUtc": booking.start_utc.isoformat(),
        "endUtc": booking.end_utc.isoformat(),
        "eventTypeId": booking.event_type_id,
        "attendee": {
            "name": attendee.name,
            "email": attendee.email,
            "notes": attendee.notes,
            "timezone": attendee.timezone,
        },
        "location": booking.location,
        "createdAt": booking.created_at.isoformat(),
        "updatedAt": booking.updated_at.isoformat(),
    }
