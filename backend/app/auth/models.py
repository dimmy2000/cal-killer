"""Pydantic request/response models for the auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    username: str
    timezone: str
    avatarUrl: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refreshToken: str


class UserRef(BaseModel):
    id: str
    email: str
    name: str
    username: str
    timezone: str
    avatarUrl: str | None = None
    createdAt: str


class AuthTokens(BaseModel):
    accessToken: str
    refreshToken: str
    user: UserRef
