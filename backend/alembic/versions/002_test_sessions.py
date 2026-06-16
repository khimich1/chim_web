"""TestSession and TestSessionStep tables.

Revision ID: 002_test_sessions
Revises: 001_initial
Create Date: 2026-06-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_test_sessions"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "test_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column(
            "track",
            sa.Enum("ege", "oge", name="exam_track", native_enum=False, length=10),
            nullable=False,
        ),
        sa.Column("variant_ref", sa.String(length=64), nullable=False),
        sa.Column("homework_assignment_id", sa.Uuid(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "in_progress",
                "completed",
                name="test_session_status",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_test_sessions_student_id"),
        "test_sessions",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_test_sessions_homework_assignment_id"),
        "test_sessions",
        ["homework_assignment_id"],
        unique=False,
    )

    op.create_table(
        "test_session_steps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("answer", sa.String(length=512), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("hint_used", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "status",
            sa.Enum(
                "unseen",
                "answered",
                "checked",
                name="step_status",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["session_id"], ["test_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "position", name="uq_step_session_position"),
    )
    op.create_index(
        op.f("ix_test_session_steps_session_id"),
        "test_session_steps",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_test_session_steps_session_id"),
        table_name="test_session_steps",
    )
    op.drop_table("test_session_steps")
    op.drop_index(
        op.f("ix_test_sessions_homework_assignment_id"),
        table_name="test_sessions",
    )
    op.drop_index(
        op.f("ix_test_sessions_student_id"),
        table_name="test_sessions",
    )
    op.drop_table("test_sessions")
