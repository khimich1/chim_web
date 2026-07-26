"""Extend upload_handoff_tokens for feedback purpose + staging.

Revision ID: 022_handoff_feedback_purpose
Revises: 021_step_answer_image_ids
Create Date: 2026-07-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "022_handoff_feedback_purpose"
down_revision: Union[str, Sequence[str], None] = "021_step_answer_image_ids"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("upload_handoff_tokens", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "purpose",
                sa.String(length=32),
                nullable=False,
                server_default="answer",
            )
        )
        batch_op.add_column(sa.Column("homework_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("teacher_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("staged_image_id", sa.Uuid(), nullable=True))
        batch_op.alter_column(
            "session_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )
        batch_op.alter_column(
            "student_id",
            existing_type=sa.Uuid(),
            nullable=True,
        )
        batch_op.alter_column(
            "position",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.create_foreign_key(
            "fk_upload_handoff_tokens_homework_id",
            "homework_assignments",
            ["homework_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_upload_handoff_tokens_teacher_id",
            "users",
            ["teacher_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_foreign_key(
            "fk_upload_handoff_tokens_staged_image_id",
            "uploaded_images",
            ["staged_image_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_upload_handoff_tokens_homework_id",
            ["homework_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_upload_handoff_tokens_teacher_id",
            ["teacher_id"],
            unique=False,
        )
        batch_op.create_check_constraint(
            "ck_upload_handoff_purpose_fks",
            "(purpose = 'answer' AND session_id IS NOT NULL AND student_id IS NOT NULL "
            "AND position IS NOT NULL AND homework_id IS NULL AND teacher_id IS NULL) OR "
            "(purpose = 'feedback' AND homework_id IS NOT NULL AND teacher_id IS NOT NULL "
            "AND session_id IS NULL AND student_id IS NULL)",
        )


def downgrade() -> None:
    with op.batch_alter_table("upload_handoff_tokens", schema=None) as batch_op:
        batch_op.drop_constraint("ck_upload_handoff_purpose_fks", type_="check")
        batch_op.drop_index("ix_upload_handoff_tokens_teacher_id")
        batch_op.drop_index("ix_upload_handoff_tokens_homework_id")
        batch_op.drop_constraint(
            "fk_upload_handoff_tokens_staged_image_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_upload_handoff_tokens_teacher_id",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_upload_handoff_tokens_homework_id",
            type_="foreignkey",
        )
        batch_op.drop_column("staged_image_id")
        batch_op.drop_column("teacher_id")
        batch_op.drop_column("homework_id")
        batch_op.drop_column("purpose")
        batch_op.alter_column(
            "position",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.alter_column(
            "student_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
        batch_op.alter_column(
            "session_id",
            existing_type=sa.Uuid(),
            nullable=False,
        )
