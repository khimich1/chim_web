"""Add partial-submit progress fields to homework_submissions.

Revision ID: 017_homework_submission_progress
Revises: 016_rag_documents
Create Date: 2026-06-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_homework_submission_progress"
down_revision: Union[str, Sequence[str], None] = "016_rag_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "homework_submissions",
        sa.Column("answered_steps", sa.Integer(), nullable=True),
    )
    op.add_column(
        "homework_submissions",
        sa.Column("total_steps", sa.Integer(), nullable=True),
    )
    op.add_column(
        "homework_submissions",
        sa.Column("completion_percent", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("homework_submissions", "completion_percent")
    op.drop_column("homework_submissions", "total_steps")
    op.drop_column("homework_submissions", "answered_steps")
