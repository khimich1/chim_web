"""Tutor chat sessions and messages.

Revision ID: 004_tutor
Revises: 003_homework
Create Date: 2026-06-17

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_tutor"
down_revision: Union[str, Sequence[str], None] = "003_homework"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tutor_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role_context",
            sa.Enum("teacher", "student", name="user_role", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("page_context", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tutor_sessions_user_id"),
        "tutor_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "tutor_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "user",
                "assistant",
                name="tutor_message_role",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["session_id"], ["tutor_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tutor_messages_session_id"),
        "tutor_messages",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tutor_messages_session_id"), table_name="tutor_messages")
    op.drop_table("tutor_messages")
    op.drop_index(op.f("ix_tutor_sessions_user_id"), table_name="tutor_sessions")
    op.drop_table("tutor_sessions")
