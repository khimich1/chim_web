"""Custom teacher themes, tasks, uploads, and TestSession extensions (Phase 14).

Revision ID: 011_custom_tasks
Revises: 010_student_onboarding
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_custom_tasks"
down_revision: Union[str, Sequence[str], None] = "010_student_onboarding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "teacher_themes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_teacher_themes_teacher_id"),
        "teacher_themes",
        ["teacher_id"],
        unique=False,
    )

    op.create_table(
        "custom_tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("theme_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=True),
        sa.Column(
            "sort_order",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "grading_mode",
            sa.Enum(
                "auto",
                "self_check",
                name="grading_mode",
                native_enum=False,
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("question_blocks", sa.JSON(), nullable=False),
        sa.Column("reference_answer", sa.JSON(), nullable=True),
        sa.Column("correct_value", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["theme_id"], ["teacher_themes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_custom_tasks_theme_id"),
        "custom_tasks",
        ["theme_id"],
        unique=False,
    )

    op.create_table(
        "uploaded_images",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_uploaded_images_owner_id"),
        "uploaded_images",
        ["owner_id"],
        unique=False,
    )

    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "source",
                sa.Enum(
                    "exam",
                    "custom",
                    name="test_session_source",
                    native_enum=False,
                    length=10,
                ),
                nullable=False,
                server_default="exam",
            )
        )
        batch_op.add_column(
            sa.Column("custom_theme_id", sa.Uuid(), nullable=True)
        )
        batch_op.add_column(sa.Column("custom_task_ids", sa.JSON(), nullable=True))
        batch_op.create_foreign_key(
            "fk_test_sessions_custom_theme_id",
            "teacher_themes",
            ["custom_theme_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            op.f("ix_test_sessions_custom_theme_id"),
            ["custom_theme_id"],
        )

    with op.batch_alter_table("test_session_steps") as batch_op:
        batch_op.add_column(sa.Column("custom_task_id", sa.Uuid(), nullable=True))
        batch_op.alter_column(
            "test_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.create_foreign_key(
            "fk_test_session_steps_custom_task_id",
            "custom_tasks",
            ["custom_task_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            op.f("ix_test_session_steps_custom_task_id"),
            ["custom_task_id"],
        )
        batch_op.create_check_constraint(
            "ck_step_exactly_one_question_ref",
            "(test_id IS NOT NULL AND custom_task_id IS NULL) OR "
            "(test_id IS NULL AND custom_task_id IS NOT NULL)",
        )

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
                "test_by_type",
                "custom_theme",
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
                "custom_theme",
                name="homework_item_kind",
                native_enum=False,
                length=32,
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

    with op.batch_alter_table("test_session_steps") as batch_op:
        batch_op.drop_constraint(
            "ck_step_exactly_one_question_ref",
            type_="check",
        )
        batch_op.drop_index(op.f("ix_test_session_steps_custom_task_id"))
        batch_op.drop_constraint(
            "fk_test_session_steps_custom_task_id",
            type_="foreignkey",
        )
        batch_op.drop_column("custom_task_id")
        batch_op.alter_column(
            "test_id",
            existing_type=sa.Integer(),
            nullable=False,
        )

    with op.batch_alter_table("test_sessions") as batch_op:
        batch_op.drop_index(op.f("ix_test_sessions_custom_theme_id"))
        batch_op.drop_constraint(
            "fk_test_sessions_custom_theme_id",
            type_="foreignkey",
        )
        batch_op.drop_column("custom_task_ids")
        batch_op.drop_column("custom_theme_id")
        batch_op.drop_column("source")

    op.drop_index(op.f("ix_uploaded_images_owner_id"), table_name="uploaded_images")
    op.drop_table("uploaded_images")
    op.drop_index(op.f("ix_custom_tasks_theme_id"), table_name="custom_tasks")
    op.drop_table("custom_tasks")
    op.drop_index(op.f("ix_teacher_themes_teacher_id"), table_name="teacher_themes")
    op.drop_table("teacher_themes")
