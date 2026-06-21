"""Homework assignment and submission ORM models (app DB)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import HomeworkItemKind, HomeworkStatus

if TYPE_CHECKING:
    from app.models.test_session import TestSession
    from app.models.user import User


class HomeworkAssignment(Base):
    __tablename__ = "homework_assignments"

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
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
    )
    status: Mapped[HomeworkStatus] = mapped_column(
        Enum(
            HomeworkStatus,
            name="homework_status",
            native_enum=False,
            length=20,
        ),
        nullable=False,
        default=HomeworkStatus.ASSIGNED,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped[User] = relationship("User", foreign_keys=[student_id])
    teacher: Mapped[User] = relationship("User", foreign_keys=[teacher_id])
    submission: Mapped[HomeworkSubmission | None] = relationship(
        "HomeworkSubmission",
        back_populates="assignment",
        uselist=False,
        cascade="all, delete-orphan",
    )
    item_progress: Mapped[list[HomeworkItemProgress]] = relationship(
        "HomeworkItemProgress",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="HomeworkItemProgress.item_index",
    )


class HomeworkItemProgress(Base):
    """Per-item completion state for a multi-item homework assignment.

    One row per entry in ``HomeworkAssignment.items``. Lecture items are marked
    complete via an explicit "Прочитано" action; test items are completed once
    the aggregated TestSession is finished (synced lazily by the service).
    """

    __tablename__ = "homework_item_progress"
    __table_args__ = (
        UniqueConstraint(
            "assignment_id",
            "item_index",
            name="uq_item_progress_assignment_item",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("homework_assignments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_index: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[HomeworkItemKind] = mapped_column(
        Enum(
            HomeworkItemKind,
            name="homework_item_kind",
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    assignment: Mapped[HomeworkAssignment] = relationship(
        "HomeworkAssignment",
        back_populates="item_progress",
    )


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("homework_assignments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    test_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    answered_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_percent: Mapped[int | None] = mapped_column(Integer, nullable=True)

    assignment: Mapped[HomeworkAssignment] = relationship(
        "HomeworkAssignment",
        back_populates="submission",
    )
    test_session: Mapped[TestSession | None] = relationship("TestSession")
