"""Add assign_batch_id and cancelled_at on homework_assignments.

Revision ID: 020_homework_assign_batch_cancelled_at
Revises: 019_homework_templates_groups
Create Date: 2026-07-24

Adds:
- homework_assignments.assign_batch_id (UUID nullable, indexed)
- homework_assignments.cancelled_at (timestamptz nullable)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "020_homework_assign_batch_cancelled_at"
down_revision: Union[str, Sequence[str], None] = "019_homework_templates_groups"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("homework_assignments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("assign_batch_id", sa.Uuid(), nullable=True))
        batch_op.add_column(
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.create_index(
            op.f("ix_homework_assignments_assign_batch_id"),
            ["assign_batch_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("homework_assignments", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_homework_assignments_assign_batch_id"))
        batch_op.drop_column("cancelled_at")
        batch_op.drop_column("assign_batch_id")
