"""create bookings and attendees tables

Revision ID: b4008104fbae
Revises: 5048efb812ef
Create Date: 2026-07-05 18:45:26.954759

Creates the `attendees` and `bookings` tables for the Bookings domain
(Этап B). Hand-trimmed from the autogenerate output: the type drift on
`users` / `schedules` (TEXT vs String) and the missing `working_hours` /
`schedule_overrides` migrations are out of scope for this domain and will
be reconciled in the migrations finalize stage.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b4008104fbae"
down_revision: str | None = "5048efb812ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendees",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.String(length=4000), nullable=True),
        sa.Column("timezone", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_attendees_email"), "attendees", ["email"], unique=False)

    op.create_table(
        "bookings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("start_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("location", sa.String(length=20), nullable=False),
        sa.Column("manage_token_hash", sa.String(length=255), nullable=False),
        sa.Column("attendee_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["attendee_id"], ["attendees.id"]),
        sa.ForeignKeyConstraint(["event_type_id"], ["event_types.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bookings_event_type_id"), "bookings", ["event_type_id"], unique=False)
    op.create_index(op.f("ix_bookings_start_utc"), "bookings", ["start_utc"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_bookings_start_utc"), table_name="bookings")
    op.drop_index(op.f("ix_bookings_event_type_id"), table_name="bookings")
    op.drop_table("bookings")
    op.drop_index(op.f("ix_attendees_email"), table_name="attendees")
    op.drop_table("attendees")
