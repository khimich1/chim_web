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
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ExamTrack, StepStatus, TestSessionStatus

if TYPE_CHECKING:
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
    variant_ref: Mapped[str] = mapped_column(String(64), nullable=False)
    homework_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        nullable=True,
        index=True,
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
    test_id: Mapped[int] = mapped_column(Integer, nullable=False)
    answer: Mapped[str | None] = mapped_column(String(512), nullable=True)
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
