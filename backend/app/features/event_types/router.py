"""EventTypes router — `/event-types`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from app.auth.deps import CurrentUser, get_current_user
from app.core.pagination import Paginated, page_query
from app.db.session import get_session
from app.features.event_types.schemas import EventType, EventTypeCreate, EventTypeUpdate
from app.features.event_types.service import (
    create_event_type,
    delete_event_type,
    get_event_type,
    list_event_types,
    update_event_type,
)

router = APIRouter(prefix="/event-types", tags=["Event Types"])


@router.get("", status_code=200)
def list_event_types_endpoint(
    scheduleId: str | None = Query(default=None),
    _page=Depends(page_query),
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Paginated[EventType]:
    return Paginated[EventType].model_validate(
        list_event_types(
            session,
            current.id,
            schedule_id=scheduleId,
            limit=_page.limit,
            cursor=_page.cursor,
        )
    )


@router.post("", status_code=201)
def create_event_type_endpoint(
    body: EventTypeCreate,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> EventType:
    return EventType.model_validate(
        create_event_type(
            session,
            current.id,
            slug=body.slug,
            title=body.title,
            description=body.description,
            duration_min=body.durationMin,
            location=body.location,
            color=body.color,
            schedule_id=body.scheduleId,
            padding_min_before=body.paddingMinBefore,
            padding_min_after=body.paddingMinAfter,
            min_notice_min=body.minNoticeMin,
            requires_confirmation=body.requiresConfirmation,
        )
    )


@router.get("/{id}", status_code=200)
def read_event_type_endpoint(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> EventType:
    return EventType.model_validate(get_event_type(session, current.id, id))


@router.patch("/{id}", status_code=200)
def update_event_type_endpoint(
    id: str,
    body: EventTypeUpdate,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> EventType:
    return EventType.model_validate(
        update_event_type(
            session,
            current.id,
            id,
            slug=body.slug,
            title=body.title,
            description=body.description,
            duration_min=body.durationMin,
            location=body.location,
            color=body.color,
            schedule_id=body.scheduleId,
            padding_min_before=body.paddingMinBefore,
            padding_min_after=body.paddingMinAfter,
            min_notice_min=body.minNoticeMin,
            requires_confirmation=body.requiresConfirmation,
        )
    )


@router.delete("/{id}", status_code=204)
def delete_event_type_endpoint(
    id: str,
    current: CurrentUser = Depends(get_current_user),
    session=Depends(get_session),
) -> Response:
    delete_event_type(session, current.id, id)
    return Response(status_code=204)
