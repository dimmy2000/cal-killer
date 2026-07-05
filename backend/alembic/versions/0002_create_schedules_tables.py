"""create schedules tables

Revision ID: 0002_schedules
Revises: 0001_users
Create Date: 2026-07-05 19:01:00.000000

Creates the `schedules`, `working_hours`, and `schedule_overrides` tables for
the Schedules domain (Этап S). Hand-written to match the ORM in
app/db/models/schedule.py.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_schedules"
down_revision: str | None = "0001_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "schedules",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_schedules_user_id"), "schedules", ["user_id"], unique=False)

    op.create_table(
        "working_hours",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("schedule_id", sa.String(length=36), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_min", sa.Integer(), nullable=False),
        sa.Column("end_min", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_id", "day_of_week", name="uq_working_hours_day"),
    )
    op.create_index(
        op.f("ix_working_hours_schedule_id"), "working_hours", ["schedule_id"], unique=False
    )

    op.create_table(
        "schedule_overrides",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("schedule_id", sa.String(length=36), nullable=False),
        sa.Column("date", sa.String(length=10), nullable=False),
        sa.Column("start_min", sa.Integer(), nullable=False),
        sa.Column("end_min", sa.Integer(), nullable=False),
        sa.Column("available", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schedule_id", "date", name="uq_schedule_overrides_date"),
    )
    op.create_index(
        op.f("ix_schedule_overrides_schedule_id"),
        "schedule_overrides",
        ["schedule_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_schedule_overrides_schedule_id"), table_name="schedule_overrides")
    op.drop_table("schedule_overrides")
    op.drop_index(op.f("ix_working_hours_schedule_id"), table_name="working_hours")
    op.drop_table("working_hours")
    op.drop_index(op.f("ix_schedules_user_id"), table_name="schedules")
    op.drop_table("schedules")
