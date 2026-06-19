"""Activity ledger, student stats, and display_name (Phase 13, Task 58).

Revision ID: 008_activity_stats
Revises: 007_rag_embeddings
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_activity_stats"
down_revision: Union[str, Sequence[str], None] = "007_rag_embeddings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("display_name", sa.String(length=100), nullable=True),
    )

    op.create_table(
        "student_activity_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "step_correct",
                "homework_complete",
                "streak_daily",
                "streak_weekly",
                name="activity_event_type",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("ref_id", sa.String(length=64), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_id",
            "event_type",
            "ref_id",
            name="uq_activity_event_student_type_ref",
        ),
    )
    op.create_index(
        op.f("ix_student_activity_events_student_id"),
        "student_activity_events",
        ["student_id"],
        unique=False,
    )

    op.create_table(
        "student_stats",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("total_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("week_points", sa.Integer(), server_default="0", nullable=False),
        sa.Column("current_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("longest_streak", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("tasks_solved", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_id"),
    )


def downgrade() -> None:
    op.drop_table("student_stats")
    op.drop_index(
        op.f("ix_student_activity_events_student_id"),
        table_name="student_activity_events",
    )
    op.drop_table("student_activity_events")
    op.drop_column("student_profiles", "display_name")
