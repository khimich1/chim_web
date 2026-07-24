"""Normalize users.email to lowercase (login identifier).

Revision ID: 018_normalize_user_email_lowercase
Revises: 017_homework_submission_progress
Create Date: 2026-07-23

One-shot data fix so case-insensitive login works for existing accounts.
JSON/DB column name remains ``email`` (no rename).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_normalize_user_email_lowercase"
down_revision: Union[str, Sequence[str], None] = "017_homework_submission_progress"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    collisions = conn.execute(
        sa.text(
            """
            SELECT lower(email) AS login_key, COUNT(*) AS cnt
            FROM users
            GROUP BY lower(email)
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()
    if collisions:
        keys = ", ".join(str(row[0]) for row in collisions)
        raise RuntimeError(
            "Cannot normalize users.email: case collisions for: "
            f"{keys}. Resolve duplicates manually, then re-run migration."
        )

    op.execute(
        sa.text(
            "UPDATE users SET email = lower(email) WHERE email <> lower(email)"
        )
    )


def downgrade() -> None:
    # Irreversible data migration (original casing is not retained).
    pass
