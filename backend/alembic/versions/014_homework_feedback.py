"""Add homework feedback tables and uploaded_audios (SPEC §1.9.9, Task 81).

Revision ID: 014_homework_feedback
Revises: 013_upload_handoff_token
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "014_homework_feedback"
down_revision: Union[str, Sequence[str], None] = "013_upload_handoff_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "uploaded_audios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("duration_sec", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_uploaded_audios_owner_id"),
        "uploaded_audios",
        ["owner_id"],
        unique=False,
    )

    op.create_table(
        "test_session_step_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("test_session_step_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_text", sa.Text(), nullable=True),
        sa.Column("teacher_voice_id", sa.Uuid(), nullable=True),
        sa.Column("teacher_image_ids", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["teacher_voice_id"],
            ["uploaded_audios.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["test_session_step_id"],
            ["test_session_steps.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_session_step_id"),
    )
    op.create_index(
        op.f("ix_test_session_step_feedback_test_session_step_id"),
        "test_session_step_feedback",
        ["test_session_step_id"],
        unique=True,
    )

    op.create_table(
        "homework_submission_feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("homework_submission_id", sa.Uuid(), nullable=False),
        sa.Column("teacher_text", sa.Text(), nullable=True),
        sa.Column("teacher_voice_id", sa.Uuid(), nullable=True),
        sa.Column("teacher_image_ids", sa.JSON(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["homework_submission_id"],
            ["homework_submissions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["teacher_voice_id"],
            ["uploaded_audios.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("homework_submission_id"),
    )
    op.create_index(
        op.f("ix_homework_submission_feedback_homework_submission_id"),
        "homework_submission_feedback",
        ["homework_submission_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_homework_submission_feedback_homework_submission_id"),
        table_name="homework_submission_feedback",
    )
    op.drop_table("homework_submission_feedback")
    op.drop_index(
        op.f("ix_test_session_step_feedback_test_session_step_id"),
        table_name="test_session_step_feedback",
    )
    op.drop_table("test_session_step_feedback")
    op.drop_index(op.f("ix_uploaded_audios_owner_id"), table_name="uploaded_audios")
    op.drop_table("uploaded_audios")
