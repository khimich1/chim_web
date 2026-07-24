"""Replace answer_image_id with answer_image_ids JSON (multi-photo, max 3).

Revision ID: 021_step_answer_image_ids
Revises: 020_homework_assign_batch_cancelled_at
Create Date: 2026-07-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "021_step_answer_image_ids"
down_revision: Union[str, Sequence[str], None] = "020_homework_assign_batch_cancelled_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("test_session_steps", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "answer_image_ids",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, answer_image_id FROM test_session_steps "
            "WHERE answer_image_id IS NOT NULL"
        )
    ).fetchall()
    for row in rows:
        image_id = str(row[1])
        connection.execute(
            sa.text(
                "UPDATE test_session_steps "
                "SET answer_image_ids = :ids WHERE id = :id"
            ),
            {"ids": f'["{image_id}"]', "id": str(row[0])},
        )

    with op.batch_alter_table("test_session_steps", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_test_session_steps_answer_image_id"))
        batch_op.drop_constraint(
            "fk_test_session_steps_answer_image_id",
            type_="foreignkey",
        )
        batch_op.drop_column("answer_image_id")


def downgrade() -> None:
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

    connection = op.get_bind()
    rows = connection.execute(
        sa.text("SELECT id, answer_image_ids FROM test_session_steps")
    ).fetchall()
    import json

    for row in rows:
        raw = row[1]
        if isinstance(raw, str):
            ids = json.loads(raw) if raw else []
        else:
            ids = raw or []
        if not ids:
            continue
        connection.execute(
            sa.text(
                "UPDATE test_session_steps "
                "SET answer_image_id = :image_id WHERE id = :id"
            ),
            {"image_id": str(ids[0]), "id": str(row[0])},
        )

    with op.batch_alter_table("test_session_steps", schema=None) as batch_op:
        batch_op.drop_column("answer_image_ids")
