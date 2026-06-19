"""Add practice_task_type for free cross-variant test practice.

Revision ID: 009_practice_task_type
Revises: 008_activity_stats
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_practice_task_type"
down_revision: Union[str, Sequence[str], None] = "008_activity_stats"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "test_sessions",
        sa.Column("practice_task_type", sa.Integer(), nullable=True),
    )
    op.create_index(
        op.f("ix_test_sessions_practice_task_type"),
        "test_sessions",
        ["practice_task_type"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_test_sessions_practice_task_type"),
        table_name="test_sessions",
    )
    op.drop_column("test_sessions", "practice_task_type")
