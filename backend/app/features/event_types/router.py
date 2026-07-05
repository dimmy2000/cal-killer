"""EventTypes router — `/event-types`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.auth.deps import CurrentUser, get_current_user
from app.core.errors import BackendError
from app.core.pagination import Paginated, page_query
from app.features.event_types.schemas import EventType, EventTypeCreate, EventTypeUpdate

router = APIRouter(prefix="/event-types", tags=["Event Types"])


@router.get("", status_code=501)
def list_event_types(
    scheduleId: str | None = Query(default=None),
    _page=Depends(page_query),
    current: CurrentUser = Depends(get_current_user),
) -> Paginated[EventType]:
    _ = scheduleId, current
    raise BackendError(501, "not implemented")


@router.post("", status_code=501)
def create_event_type(
    body: EventTypeCreate, current: CurrentUser = Depends(get_current_user)
) -> EventType:
    _ = body, current
    raise BackendError(501, "not implemented")


@router.get("/{id}", status_code=501)
def read_event_type(id: str, current: CurrentUser = Depends(get_current_user)) -> EventType:
    _ = id, current
    raise BackendError(501, "not implemented")


@router.patch("/{id}", status_code=501)
def update_event_type(
    id: str, body: EventTypeUpdate, current: CurrentUser = Depends(get_current_user)
) -> EventType:
    _ = id, body, current
    raise BackendError(501, "not implemented")


@router.delete("/{id}", status_code=501)
def delete_event_type(id: str, current: CurrentUser = Depends(get_current_user)) -> None:
    _ = id, current
    raise BackendError(501, "not implemented")
