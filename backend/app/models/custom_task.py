"""CustomTask ORM model — teacher-authored questions (Phase 14, SPEC §1.9)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import GradingMode

if TYPE_CHECKING:
    from app.models.teacher_theme import TeacherTheme


class CustomTask(Base):
    __tablename__ = "custom_tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    theme_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teacher_themes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    grading_mode: Mapped[GradingMode] = mapped_column(
        Enum(
            GradingMode,
            name="grading_mode",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=GradingMode.AUTO,
    )
    question_blocks: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
        default=list,
    )
    reference_answer: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=True,
    )
    correct_value: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    theme: Mapped[TeacherTheme] = relationship("TeacherTheme", back_populates="tasks")
