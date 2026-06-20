"""TestSession ORM models — Stepik-style stepwise test taking (app DB).

A session belongs to a student, targets one exam track and variant, and holds
an ordered list of steps (one per test question). Each step tracks the student's
latest answer, correctness, and whether a hint was requested.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import ExamTrack, StepStatus, TestSessionSource, TestSessionStatus

if TYPE_CHECKING:
    from app.models.teacher_theme import TeacherTheme
    from app.models.uploaded_image import UploadedImage
    from app.models.user import User


class TestSession(Base):
    __tablename__ = "test_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track: Mapped[ExamTrack] = mapped_column(
        Enum(ExamTrack, name="exam_track", native_enum=False, length=10),
        nullable=False,
    )
    # Null when the session aggregates test items from several variants
    # (multi-item homework, SPEC §1.7).
    variant_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Set for free practice by task type (EGE: one type across all variants).
    practice_task_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    homework_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
    )
    source: Mapped[TestSessionSource] = mapped_column(
        Enum(
            TestSessionSource,
            name="test_session_source",
            native_enum=False,
            length=10,
        ),
        nullable=False,
        default=TestSessionSource.EXAM,
        server_default=TestSessionSource.EXAM.value,
    )
    custom_theme_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teacher_themes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    custom_task_ids: Mapped[list[str] | None] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=True,
    )
    status: Mapped[TestSessionStatus] = mapped_column(
        Enum(
            TestSessionStatus,
            name="test_session_status",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=TestSessionStatus.IN_PROGRESS,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    student: Mapped[User] = relationship("User")
    custom_theme: Mapped[TeacherTheme | None] = relationship("TeacherTheme")
    steps: Mapped[list[TestSessionStep]] = relationship(
        "TestSessionStep",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TestSessionStep.position",
    )


class TestSessionStep(Base):
    __tablename__ = "test_session_steps"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_step_session_position"),
        CheckConstraint(
            "(test_id IS NOT NULL AND custom_task_id IS NULL) OR "
            "(test_id IS NULL AND custom_task_id IS NOT NULL)",
            name="ck_step_exactly_one_question_ref",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    test_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    custom_task_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("custom_tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    answer: Mapped[str | None] = mapped_column(String(512), nullable=True)
    answer_image_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("uploaded_images.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hint_used: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    status: Mapped[StepStatus] = mapped_column(
        Enum(StepStatus, name="step_status", native_enum=False, length=20),
        nullable=False,
        default=StepStatus.UNSEEN,
    )
    checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    session: Mapped[TestSession] = relationship(
        "TestSession",
        back_populates="steps",
    )
    answer_image: Mapped[UploadedImage | None] = relationship("UploadedImage")
