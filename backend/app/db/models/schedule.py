"""Schedule / WorkingHours / ScheduleOverride ORM models — skeleton."""

from __future__ import annotations

from app.db.base import Base


class Schedule(Base):
    __tablename__ = "schedules"


class ScheduleOverride(Base):
    __tablename__ = "schedule_overrides"
