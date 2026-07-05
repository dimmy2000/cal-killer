"""Schedules router — `/schedules`, `/schedules/{id}/overrides`."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.auth.deps import CurrentUser, get_current_user
from app.core.pagination import Paginated, page_query
from app.db.session import get_session
from app.features.schedules.schemas import (
    Schedule,
    ScheduleCreate,
    ScheduleOverride,
    ScheduleUpdate,
)
from app.features.schedules.service import (
    add_override,
    create_schedule,
    delete_schedule,
    get_schedule,
    list_overrides,
    list_schedules,
    remove_override,
    update_schedule,
)

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("", status_code=200)
def list_schedules_endpoint(
    _page=Depends(page_query),
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Paginated[Schedule]:
    return Paginated[Schedule].model_validate(
        list_schedules(
            session,
            current.id,
            limit=_page.limit,
            cursor=_page.cursor,
        )
    )


@router.post("", status_code=201)
def create_schedule_endpoint(
    body: ScheduleCreate,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Schedule:
    return Schedule.model_validate(
        create_schedule(
            session,
            current.id,
            name=body.name,
            timezone=body.timezone,
            working_hours=[wh.model_dump() for wh in body.workingHours],
            overrides=([ov.model_dump() for ov in body.overrides] if body.overrides else None),
        )
    )


@router.get("/{id}", status_code=200)
def read_schedule(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Schedule:
    return Schedule.model_validate(get_schedule(session, current.id, id))


@router.patch("/{id}", status_code=200)
def update_schedule_endpoint(
    id: str,
    body: ScheduleUpdate,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Schedule:
    return Schedule.model_validate(
        update_schedule(
            session,
            current.id,
            id,
            name=body.name,
            timezone=body.timezone,
            working_hours=(
                [wh.model_dump() for wh in body.workingHours]
                if body.workingHours is not None
                else None
            ),
        )
    )


@router.delete("/{id}", status_code=204)
def delete_schedule_endpoint(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Response:
    delete_schedule(session, current.id, id)
    return Response(status_code=204)


@router.get("/{id}/overrides", status_code=200)
def list_overrides_endpoint(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> list[ScheduleOverride]:
    return [ScheduleOverride.model_validate(o) for o in list_overrides(session, current.id, id)]


@router.post("/{id}/overrides", status_code=200)
def add_override_endpoint(
    id: str,
    body: ScheduleOverride,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> ScheduleOverride:
    return ScheduleOverride.model_validate(
        add_override(session, current.id, id, override=body.model_dump())
    )


@router.delete("/{id}/overrides/{date}", status_code=204)
def remove_override_endpoint(
    id: str,
    date: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Response:
    remove_override(session, current.id, id, date)
    return Response(status_code=204)
