"""Pydantic schemas for the Public booking feature."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

EventLocation = Literal["online", "in_person", "phone"]


class PublicEventType(BaseModel):
    title: str
    description: str | None = None
    durationMin: int
    location: EventLocation
    color: str | None = None
    ownerName: str
    ownerTimezone: str
    requiresConfirmation: bool


class AttendeeCreate(BaseModel):
    name: str
    email: str
    notes: str | None = None
    timezone: str


class PublicBookingCreate(BaseModel):
    attendee: AttendeeCreate
    startUtc: str


class Slot(BaseModel):
    startUtc: str
    endUtc: str


class Booking(BaseModel):
    id: str
    status: str
    startUtc: str
    endUtc: str
    eventTypeId: str
    attendee: AttendeeCreate
    location: EventLocation
    createdAt: str


class BookingWithToken(BaseModel):
    booking: Booking
    manageToken: str


class ManageToken(BaseModel):
    token: str


class RescheduleRequest(BaseModel):
    token: str
    startUtc: str
