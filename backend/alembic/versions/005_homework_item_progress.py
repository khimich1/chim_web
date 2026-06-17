"""Per-item homework progress + nullable test session variant_ref.

Revision ID: 005_hw_progress
Revises: 004_tutor
Create Date: 2026-06-17

Supports multi-item homework (SPEC §1.7): each assignment item gets a progress
row, and an aggregated TestSession spanning several variants stores
``variant_ref = NULL``.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_hw_progress"
down_revision: Union[str, Sequence[str], None] = "004_tutor"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "homework_item_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("item_index", sa.Integer(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "lecture",
                "test_variant",
                "test_partial",
                name="homework_item_kind",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["assignment_id"], ["homework_assignments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "assignment_id",
            "item_index",
            name="uq_item_progress_assignment_item",
        ),
    )
    op.create_index(
        op.f("ix_homework_item_progress_assignment_id"),
        "homework_item_progress",
        ["assignment_id"],
        unique=False,
    )

    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.alter_column(
            "variant_ref",
            existing_type=sa.String(length=64),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.alter_column(
            "variant_ref",
            existing_type=sa.String(length=64),
            nullable=False,
        )

    op.drop_index(
        op.f("ix_homework_item_progress_assignment_id"),
        table_name="homework_item_progress",
    )
    op.drop_table("homework_item_progress")
