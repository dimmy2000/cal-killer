"""Public router — `/public/*` (no auth).

Route order matters: the `/bookings/...` paths are registered before the
`/{ownerSlug}/{eventSlug}` catch-alls so they aren't shadowed.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.errors import BackendError
from app.features.public.schemas import (
    Booking,
    BookingWithToken,
    ManageToken,
    PublicBookingCreate,
    PublicEventType,
    RescheduleRequest,
    Slot,
)

router = APIRouter(prefix="/public", tags=["Public"])


# --- /public/bookings/{id} ... (registered first) -------------------------


@router.get("/bookings/{id}", status_code=501)
def get_booking(id: str, token: str = Query()) -> Booking:
    _ = id, token
    raise BackendError(501, "not implemented")


@router.post("/bookings/{id}/confirm", status_code=501)
def confirm_booking(id: str, body: ManageToken) -> Booking:
    _ = id, body
    raise BackendError(501, "not implemented")


@router.post("/bookings/{id}/cancel", status_code=501)
def cancel_booking(id: str, body: ManageToken) -> Booking:
    _ = id, body
    raise BackendError(501, "not implemented")


@router.post("/bookings/{id}/reschedule", status_code=501)
def reschedule_booking(id: str, body: RescheduleRequest) -> BookingWithToken:
    _ = id, body
    raise BackendError(501, "not implemented")


# --- /public/{ownerSlug}/{eventSlug} ... ----------------------------------


@router.get("/{ownerSlug}/{eventSlug}", status_code=501)
def get_event(ownerSlug: str, eventSlug: str) -> PublicEventType:
    _ = ownerSlug, eventSlug
    raise BackendError(501, "not implemented")


@router.get("/{ownerSlug}/{eventSlug}/slots", status_code=501)
def get_slots(
    ownerSlug: str,
    eventSlug: str,
    from_: str = Query(alias="from"),
    to: str = Query(),
    tz: str | None = Query(default=None),
) -> list[Slot]:
    _ = ownerSlug, eventSlug, from_, to, tz
    raise BackendError(501, "not implemented")


@router.post("/{ownerSlug}/{eventSlug}/bookings", status_code=501)
def create_booking(ownerSlug: str, eventSlug: str, body: PublicBookingCreate) -> BookingWithToken:
    _ = ownerSlug, eventSlug, body
    raise BackendError(501, "not implemented")
