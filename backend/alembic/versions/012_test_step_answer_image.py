"""Add answer_image_id to test_session_steps (SPEC §1.9.8, Task 75).

Revision ID: 012_test_step_answer_image
Revises: 011_custom_tasks
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_test_step_answer_image"
down_revision: Union[str, Sequence[str], None] = "011_custom_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("test_session_steps", schema=None) as batch_op:
        batch_op.add_column(sa.Column("answer_image_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_test_session_steps_answer_image_id",
            "uploaded_images",
            ["answer_image_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            batch_op.f("ix_test_session_steps_answer_image_id"),
            ["answer_image_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("test_session_steps", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_test_session_steps_answer_image_id"))
        batch_op.drop_constraint(
            "fk_test_session_steps_answer_image_id",
            type_="foreignkey",
        )
        batch_op.drop_column("answer_image_id")
