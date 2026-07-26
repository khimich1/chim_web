"""Add pass/answered question id lists on neuroquiz chunk attempts.

Revision ID: 024_neuroquiz_attempt_pass
Revises: 023_neuroquiz
Create Date: 2026-07-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "024_neuroquiz_attempt_pass"
down_revision: Union[str, Sequence[str], None] = "023_neuroquiz"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("neuroquiz_chunk_attempts", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "pass_question_ids",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "answered_question_ids",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("neuroquiz_chunk_attempts", schema=None) as batch_op:
        batch_op.drop_column("answered_question_ids")
        batch_op.drop_column("pass_question_ids")
