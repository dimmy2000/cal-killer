"""Pydantic schemas for the Users feature."""

from __future__ import annotations

from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    name: str
    username: str
    timezone: str
    avatarUrl: str | None = None
    createdAt: str


class UserUpdate(BaseModel):
    email: str | None = None
    name: str | None = None
    username: str | None = None
    timezone: str | None = None
    avatarUrl: str | None = None


class PasswordChange(BaseModel):
    currentPassword: str
    newPassword: str
