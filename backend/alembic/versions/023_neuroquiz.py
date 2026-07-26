"""Alembic: neuroquiz questions, chunk attempts, votes.

Revision ID: 023_neuroquiz
Revises: 022_handoff_feedback_purpose
Create Date: 2026-07-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "023_neuroquiz"
down_revision: Union[str, Sequence[str], None] = "022_handoff_feedback_purpose"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "neuroquiz_questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("chunk_idx", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=False),
        sa.Column("correct_option_id", sa.String(length=64), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column(
            "source",
            sa.Enum(
                "qa_pair",
                "lecture_gen",
                name="neuroquiz_question_source",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "retired",
                name="neuroquiz_question_status",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_neuroquiz_questions_topic_chunk_status",
        "neuroquiz_questions",
        ["topic", "chunk_idx", "status"],
        unique=False,
    )

    op.create_table(
        "neuroquiz_chunk_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("chunk_idx", sa.Integer(), nullable=False),
        sa.Column(
            "completed",
            sa.Boolean(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_neuroquiz_chunk_attempts_student_id"),
        "neuroquiz_chunk_attempts",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_neuroquiz_chunk_attempts_student_topic_chunk",
        "neuroquiz_chunk_attempts",
        ["student_id", "topic", "chunk_idx"],
        unique=False,
    )

    op.create_table(
        "neuroquiz_votes",
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column(
            "value",
            sa.Enum(
                "like",
                "dislike",
                name="neuroquiz_vote_value",
                native_enum=False,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["neuroquiz_questions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("student_id", "question_id"),
        sa.UniqueConstraint(
            "student_id",
            "question_id",
            name="uq_neuroquiz_vote_student_question",
        ),
    )


def downgrade() -> None:
    op.drop_table("neuroquiz_votes")
    op.drop_index(
        "ix_neuroquiz_chunk_attempts_student_topic_chunk",
        table_name="neuroquiz_chunk_attempts",
    )
    op.drop_index(
        op.f("ix_neuroquiz_chunk_attempts_student_id"),
        table_name="neuroquiz_chunk_attempts",
    )
    op.drop_table("neuroquiz_chunk_attempts")
    op.drop_index(
        "ix_neuroquiz_questions_topic_chunk_status",
        table_name="neuroquiz_questions",
    )
    op.drop_table("neuroquiz_questions")
