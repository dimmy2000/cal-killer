"""create event_types table

Revision ID: 5048efb812ef
Revises: 0002_schedules
Create Date: 2026-07-05 18:21:13.957680
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5048efb812ef"
down_revision: str | None = "0002_schedules"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "event_types",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("schedule_id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=2000), nullable=True),
        sa.Column("duration_min", sa.Integer(), nullable=False),
        sa.Column("location", sa.String(length=20), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("padding_min_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("padding_min_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("min_notice_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "requires_confirmation",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["schedule_id"], ["schedules.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slug", name="uq_event_types_user_slug"),
    )
    op.create_index(op.f("ix_event_types_user_id"), "event_types", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_event_types_schedule_id"),
        "event_types",
        ["schedule_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_event_types_schedule_id"), table_name="event_types")
    op.drop_index(op.f("ix_event_types_user_id"), table_name="event_types")
    op.drop_table("event_types")
