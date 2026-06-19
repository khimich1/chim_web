"""Student onboarding fields on student_profiles.

Revision ID: 010_student_onboarding
Revises: 009_practice_task_type
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_student_onboarding"
down_revision: Union[str, Sequence[str], None] = "009_practice_task_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_DEFAULT_CHECKLIST = '{"login": false, "first_action": false, "lecture": false}'


def upgrade() -> None:
    op.add_column(
        "student_profiles",
        sa.Column("first_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "student_profiles",
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "student_profiles",
        sa.Column(
            "onboarding_checklist",
            sa.JSON(),
            nullable=False,
            server_default=sa.text(f"'{_DEFAULT_CHECKLIST}'"),
        ),
    )

    # Existing students should not see the welcome screen.
    op.execute(
        """
        UPDATE student_profiles
        SET onboarding_completed_at = CURRENT_TIMESTAMP,
            onboarding_checklist = '{"login": true, "first_action": true, "lecture": true}'
        WHERE onboarding_completed_at IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("student_profiles", "onboarding_checklist")
    op.drop_column("student_profiles", "onboarding_completed_at")
    op.drop_column("student_profiles", "first_login_at")
