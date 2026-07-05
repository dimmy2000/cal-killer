"""EventType ORM model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EventType(Base):
    __tablename__ = "event_types"
    __table_args__ = (UniqueConstraint("user_id", "slug", name="uq_event_types_user_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    schedule_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schedules.id"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    duration_min: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(20), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    padding_min_before: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    padding_min_after: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_notice_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    requires_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
