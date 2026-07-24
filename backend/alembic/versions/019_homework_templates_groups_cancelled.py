"""Homework templates, student groups, assignment provenance, cancelled status.

Revision ID: 019_homework_templates_groups
Revises: 018_normalize_user_email_lowercase
Create Date: 2026-07-23

Adds:
- homework_templates
- student_groups / student_group_members
- homework_assignments.template_id (ON DELETE SET NULL)
- homework_assignments.source_group_id (ON DELETE SET NULL)

Status value ``cancelled`` is stored as VARCHAR (native_enum=False); no
schema ALTER needed beyond the Python enum.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "019_homework_templates_groups"
down_revision: Union[str, Sequence[str], None] = "018_normalize_user_email_lowercase"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "homework_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_homework_templates_teacher_id"),
        "homework_templates",
        ["teacher_id"],
        unique=False,
    )

    op.create_table(
        "student_groups",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_student_groups_teacher_id"),
        "student_groups",
        ["teacher_id"],
        unique=False,
    )

    op.create_table(
        "student_group_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("student_user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["student_groups.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["student_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "student_user_id",
            name="uq_student_group_members_student_user_id",
        ),
        sa.UniqueConstraint(
            "group_id",
            "student_user_id",
            name="uq_student_group_members_group_student",
        ),
    )
    op.create_index(
        op.f("ix_student_group_members_group_id"),
        "student_group_members",
        ["group_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_student_group_members_student_user_id"),
        "student_group_members",
        ["student_user_id"],
        unique=False,
    )

    with op.batch_alter_table("homework_assignments", schema=None) as batch_op:
        batch_op.add_column(sa.Column("template_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("source_group_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_homework_assignments_template_id",
            "homework_templates",
            ["template_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_homework_assignments_source_group_id",
            "student_groups",
            ["source_group_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            op.f("ix_homework_assignments_template_id"),
            ["template_id"],
            unique=False,
        )
        batch_op.create_index(
            op.f("ix_homework_assignments_source_group_id"),
            ["source_group_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("homework_assignments", schema=None) as batch_op:
        batch_op.drop_index(op.f("ix_homework_assignments_source_group_id"))
        batch_op.drop_index(op.f("ix_homework_assignments_template_id"))
        batch_op.drop_constraint(
            "fk_homework_assignments_source_group_id", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_homework_assignments_template_id", type_="foreignkey"
        )
        batch_op.drop_column("source_group_id")
        batch_op.drop_column("template_id")

    op.drop_index(
        op.f("ix_student_group_members_student_user_id"),
        table_name="student_group_members",
    )
    op.drop_index(
        op.f("ix_student_group_members_group_id"),
        table_name="student_group_members",
    )
    op.drop_table("student_group_members")
    op.drop_index(op.f("ix_student_groups_teacher_id"), table_name="student_groups")
    op.drop_table("student_groups")
    op.drop_index(
        op.f("ix_homework_templates_teacher_id"),
        table_name="homework_templates",
    )
    op.drop_table("homework_templates")
