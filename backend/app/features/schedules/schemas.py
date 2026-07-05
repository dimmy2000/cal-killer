"""Pydantic schemas for the Schedules feature."""

from __future__ import annotations

from pydantic import BaseModel


class WorkingHours(BaseModel):
    dayOfWeek: int
    startMin: int
    endMin: int


class ScheduleOverride(BaseModel):
    date: str
    startMin: int
    endMin: int
    available: bool


class Schedule(BaseModel):
    id: str
    name: str
    timezone: str
    isDefault: bool
    workingHours: list[WorkingHours]
    overrides: list[ScheduleOverride]
    createdAt: str


class ScheduleCreate(BaseModel):
    name: str
    timezone: str
    isDefault: bool | None = None
    workingHours: list[WorkingHours]
    overrides: list[ScheduleOverride] | None = None


class ScheduleUpdate(BaseModel):
    name: str | None = None
    timezone: str | None = None
    isDefault: bool | None = None
    workingHours: list[WorkingHours] | None = None
