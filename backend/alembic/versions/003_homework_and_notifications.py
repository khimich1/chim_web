"""Homework assignments, submissions, and notifications.

Revision ID: 003_homework
Revises: 002_test_sessions
Create Date: 2026-06-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_homework"
down_revision: Union[str, Sequence[str], None] = "002_test_sessions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "homework_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "assigned",
                "in_progress",
                "submitted",
                "reviewed",
                name="homework_status",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_homework_assignments_student_id"),
        "homework_assignments",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_homework_assignments_teacher_id"),
        "homework_assignments",
        ["teacher_id"],
        unique=False,
    )

    op.create_table(
        "homework_submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("test_session_id", sa.Uuid(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("max_score", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["homework_assignments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["test_session_id"], ["test_sessions.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id"),
    )
    op.create_index(
        op.f("ix_homework_submissions_assignment_id"),
        "homework_submissions",
        ["assignment_id"],
        unique=True,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "homework_submitted",
                name="notification_type",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notifications_user_id"),
        "notifications",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(
        op.f("ix_homework_submissions_assignment_id"),
        table_name="homework_submissions",
    )
    op.drop_table("homework_submissions")
    op.drop_index(
        op.f("ix_homework_assignments_teacher_id"),
        table_name="homework_assignments",
    )
    op.drop_index(
        op.f("ix_homework_assignments_student_id"),
        table_name="homework_assignments",
    )
    op.drop_table("homework_assignments")
