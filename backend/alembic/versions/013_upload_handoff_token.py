"""Add upload_handoff_tokens table (SPEC §1.9.9, Task 79).

Revision ID: 013_upload_handoff_token
Revises: 012_test_step_answer_image
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_upload_handoff_token"
down_revision: Union[str, Sequence[str], None] = "012_test_step_answer_image"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "upload_handoff_tokens",
        sa.Column("token", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["test_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(
        op.f("ix_upload_handoff_tokens_session_id"),
        "upload_handoff_tokens",
        ["session_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_upload_handoff_tokens_student_id"),
        "upload_handoff_tokens",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_upload_handoff_tokens_session_position",
        "upload_handoff_tokens",
        ["session_id", "position"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_upload_handoff_tokens_session_position",
        table_name="upload_handoff_tokens",
    )
    op.drop_index(
        op.f("ix_upload_handoff_tokens_student_id"),
        table_name="upload_handoff_tokens",
    )
    op.drop_index(
        op.f("ix_upload_handoff_tokens_session_id"),
        table_name="upload_handoff_tokens",
    )
    op.drop_table("upload_handoff_tokens")
