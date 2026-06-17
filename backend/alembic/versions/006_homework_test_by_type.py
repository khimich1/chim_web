"""Add test_by_type homework item kind.

Revision ID: 006_test_by_type
Revises: 005_hw_progress
Create Date: 2026-06-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_test_by_type"
down_revision: Union[str, Sequence[str], None] = "005_hw_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("homework_item_progress", schema=None) as batch_op:
        batch_op.alter_column(
            "kind",
            existing_type=sa.Enum(
                "lecture",
                "test_variant",
                "test_partial",
                name="homework_item_kind",
                native_enum=False,
                length=20,
            ),
            type_=sa.Enum(
                "lecture",
                "test_variant",
                "test_partial",
                "test_by_type",
                name="homework_item_kind",
                native_enum=False,
                length=32,
            ),
            existing_nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("homework_item_progress", schema=None) as batch_op:
        batch_op.alter_column(
            "kind",
            existing_type=sa.Enum(
                "lecture",
                "test_variant",
                "test_partial",
                "test_by_type",
                name="homework_item_kind",
                native_enum=False,
                length=32,
            ),
            type_=sa.Enum(
                "lecture",
                "test_variant",
                "test_partial",
                name="homework_item_kind",
                native_enum=False,
                length=20,
            ),
            existing_nullable=False,
        )
