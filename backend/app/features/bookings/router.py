"""Bookings router — `/bookings` (owner)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.auth.deps import CurrentUser, get_current_user
from app.core.errors import BackendError
from app.core.pagination import Paginated, page_query
from app.db.session import get_session
from app.features.bookings.schemas import Booking, RescheduleBody
from app.features.bookings.service import (
    cancel_booking,
    get_booking,
    list_bookings,
    reschedule_booking_owner,
)


def _parse_query_dt(value: str | None, field: str) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BackendError(400, f"invalid {field}", details=value) from exc


router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", status_code=200)
def list_bookings_endpoint(
    status: str | None = Query(default=None),
    eventTypeId: str | None = Query(default=None),
    attendeeEmail: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    _page=Depends(page_query),
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Paginated[Booking]:
    return Paginated[Booking].model_validate(
        list_bookings(
            session,
            current.id,
            status=status,
            event_type_id=eventTypeId,
            attendee_email=attendeeEmail,
            from_=_parse_query_dt(from_, "from"),
            to=_parse_query_dt(to, "to"),
            limit=_page.limit,
            cursor=_page.cursor,
        )
    )


@router.get("/{id}", status_code=200)
def read_booking_endpoint(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Booking:
    return Booking.model_validate(get_booking(session, current.id, id))


@router.post("/{id}/cancel", status_code=200)
def cancel_booking_endpoint(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Booking:
    return Booking.model_validate(cancel_booking(session, current.id, id))


@router.post("/{id}/reschedule", status_code=200)
def reschedule_booking_endpoint(
    id: str,
    body: RescheduleBody,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Booking:
    return Booking.model_validate(
        reschedule_booking_owner(session, current.id, id, start_utc=body.startUtc)
    )
