"""Pydantic schemas for the EventTypes feature."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

EventLocation = Literal["online", "in_person", "phone"]


class EventType(BaseModel):
    id: str
    slug: str
    title: str
    description: str | None = None
    durationMin: int
    location: EventLocation
    color: str | None = None
    scheduleId: str
    paddingMinBefore: int
    paddingMinAfter: int
    minNoticeMin: int
    requiresConfirmation: bool
    createdAt: str


class EventTypeCreate(BaseModel):
    slug: str
    title: str
    description: str | None = None
    durationMin: int
    location: EventLocation
    color: str | None = None
    scheduleId: str
    paddingMinBefore: int | None = None
    paddingMinAfter: int | None = None
    minNoticeMin: int | None = None
    requiresConfirmation: bool | None = None


class EventTypeUpdate(BaseModel):
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    durationMin: int | None = None
    location: EventLocation | None = None
    color: str | None = None
    scheduleId: str | None = None
    paddingMinBefore: int | None = None
    paddingMinAfter: int | None = None
    minNoticeMin: int | None = None
    requiresConfirmation: bool | None = None
