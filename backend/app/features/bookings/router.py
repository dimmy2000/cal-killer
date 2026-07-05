"""Bookings router — `/bookings` (owner)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.deps import CurrentUser, get_current_user
from app.core.errors import BackendError
from app.core.pagination import Paginated, page_query
from app.features.bookings.schemas import Booking, RescheduleBody

router = APIRouter(prefix="/bookings", tags=["Bookings"])


@router.get("", status_code=501)
def list_bookings(
    status: str | None = Query(default=None),
    eventTypeId: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
    _page=Depends(page_query),
    current: CurrentUser = Depends(get_current_user),
) -> Paginated[Booking]:
    _ = status, eventTypeId, from_, to, current
    raise BackendError(501, "not implemented")


@router.get("/{id}", status_code=501)
def read_booking(id: str, current: CurrentUser = Depends(get_current_user)) -> Booking:
    _ = id, current
    raise BackendError(501, "not implemented")


@router.post("/{id}/cancel", status_code=501)
def cancel_booking(id: str, current: CurrentUser = Depends(get_current_user)) -> Booking:
    _ = id, current
    raise BackendError(501, "not implemented")


@router.post("/{id}/reschedule", status_code=501)
def reschedule_booking(
    id: str, body: RescheduleBody, current: CurrentUser = Depends(get_current_user)
) -> Booking:
    _ = id, body, current
    raise BackendError(501, "not implemented")
