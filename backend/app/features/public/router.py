"""Public router — `/public/*` (no auth).

Route order matters: the `/bookings/...` paths are registered before the
`/{ownerSlug}/{eventSlug}` catch-alls so they aren't shadowed.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.db.session import get_session
from app.features.public.schemas import (
    Booking,
    BookingWithToken,
    ManageToken,
    PublicBookingCreate,
    PublicEventType,
    RescheduleRequest,
    Slot,
)
from app.features.public.service import (
    cancel_public_booking,
    confirm_booking,
    create_booking,
    get_public_booking,
    get_public_event,
    get_slots,
    reschedule_public_booking,
)

router = APIRouter(prefix="/public", tags=["Public"])


# --- /public/bookings/{id} ... (registered first) -------------------------


@router.get("/bookings/{id}", status_code=200)
def get_booking_endpoint(
    id: str,
    token: str = Query(),
    session=Depends(get_session),
) -> Booking:
    return Booking.model_validate(get_public_booking(session, id, token))


@router.post("/bookings/{id}/confirm", status_code=200)
def confirm_booking_endpoint(
    id: str,
    body: ManageToken,
    session=Depends(get_session),
) -> Booking:
    return Booking.model_validate(confirm_booking(session, id, body.token))


@router.post("/bookings/{id}/cancel", status_code=200)
def cancel_booking_endpoint(
    id: str,
    body: ManageToken,
    session=Depends(get_session),
) -> Booking:
    return Booking.model_validate(cancel_public_booking(session, id, body.token))


@router.post("/bookings/{id}/reschedule", status_code=200)
def reschedule_booking_endpoint(
    id: str,
    body: RescheduleRequest,
    session=Depends(get_session),
) -> BookingWithToken:
    return BookingWithToken.model_validate(
        reschedule_public_booking(session, id, body.token, body.startUtc)
    )


# --- /public/{ownerSlug}/{eventSlug} ... ----------------------------------


@router.get("/{ownerSlug}/{eventSlug}", status_code=200)
def get_event_endpoint(
    ownerSlug: str,
    eventSlug: str,
    session=Depends(get_session),
) -> PublicEventType:
    return PublicEventType.model_validate(get_public_event(session, ownerSlug, eventSlug))


@router.get("/{ownerSlug}/{eventSlug}/slots", status_code=200)
def get_slots_endpoint(
    ownerSlug: str,
    eventSlug: str,
    from_: str = Query(alias="from"),
    to: str = Query(),
    tz: str | None = Query(default=None),
    session=Depends(get_session),
) -> list[Slot]:
    _ = tz  # tz is informational; the schedule's timezone drives compilation
    return [
        Slot.model_validate(s)
        for s in get_slots(session, ownerSlug, eventSlug, from_str=from_, to_str=to)
    ]


@router.post("/{ownerSlug}/{eventSlug}/bookings", status_code=200)
def create_booking_endpoint(
    ownerSlug: str,
    eventSlug: str,
    body: PublicBookingCreate,
    session=Depends(get_session),
) -> BookingWithToken:
    return BookingWithToken.model_validate(
        create_booking(
            session,
            ownerSlug,
            eventSlug,
            attendee=body.attendee.model_dump(),
            start_utc_str=body.startUtc,
        )
    )
