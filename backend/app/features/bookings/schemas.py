"""Pydantic schemas for the Bookings feature."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

BookingStatus = Literal["pending", "confirmed", "cancelled", "rescheduled"]


class Attendee(BaseModel):
    name: str
    email: str
    notes: str | None = None
    timezone: str


class Booking(BaseModel):
    id: str
    status: BookingStatus
    startUtc: str
    endUtc: str
    eventTypeId: str
    attendee: Attendee
    location: str
    createdAt: str
    updatedAt: str


class RescheduleBody(BaseModel):
    startUtc: str
