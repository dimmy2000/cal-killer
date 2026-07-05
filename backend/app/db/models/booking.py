"""Booking / Attendee ORM models — skeleton."""

from __future__ import annotations

from app.db.base import Base


class Booking(Base):
    __tablename__ = "bookings"


class Attendee(Base):
    __tablename__ = "attendees"
