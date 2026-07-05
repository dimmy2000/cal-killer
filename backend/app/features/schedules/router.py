"""Schedules router — `/schedules`, `/schedules/{id}/overrides`."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.deps import CurrentUser, get_current_user
from app.core.errors import BackendError
from app.core.pagination import Paginated, page_query
from app.features.schedules.schemas import (
    Schedule,
    ScheduleCreate,
    ScheduleOverride,
    ScheduleUpdate,
)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("", status_code=501)
def list_schedules(
    _page=Depends(page_query),
    current: CurrentUser = Depends(get_current_user),
) -> Paginated[Schedule]:
    _ = current
    raise BackendError(501, "not implemented")


@router.post("", status_code=501)
def create_schedule(
    body: ScheduleCreate, current: CurrentUser = Depends(get_current_user)
) -> Schedule:
    _ = body, current
    raise BackendError(501, "not implemented")


@router.get("/{id}", status_code=501)
def read_schedule(id: str, current: CurrentUser = Depends(get_current_user)) -> Schedule:
    _ = id, current
    raise BackendError(501, "not implemented")


@router.patch("/{id}", status_code=501)
def update_schedule(
    id: str, body: ScheduleUpdate, current: CurrentUser = Depends(get_current_user)
) -> Schedule:
    _ = id, body, current
    raise BackendError(501, "not implemented")


@router.delete("/{id}", status_code=501)
def delete_schedule(id: str, current: CurrentUser = Depends(get_current_user)) -> None:
    _ = id, current
    raise BackendError(501, "not implemented")


@router.get("/{id}/overrides", status_code=501)
def list_overrides(
    id: str, current: CurrentUser = Depends(get_current_user)
) -> list[ScheduleOverride]:
    _ = id, current
    raise BackendError(501, "not implemented")


@router.post("/{id}/overrides", status_code=501)
def add_override(
    id: str, body: ScheduleOverride, current: CurrentUser = Depends(get_current_user)
) -> ScheduleOverride:
    _ = id, body, current
    raise BackendError(501, "not implemented")


@router.delete("/{id}/overrides/{date}", status_code=501)
def remove_override(id: str, date: str, current: CurrentUser = Depends(get_current_user)) -> None:
    _ = id, date, current
    raise BackendError(501, "not implemented")
