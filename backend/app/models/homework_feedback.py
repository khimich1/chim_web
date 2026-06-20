"""Teacher feedback on written homework (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.homework import HomeworkSubmission
    from app.models.test_session import TestSessionStep
    from app.models.user import User


class UploadedAudio(Base):
    __tablename__ = "uploaded_audios"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_sec: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped[User] = relationship("User")


class TestSessionStepFeedback(Base):
    __tablename__ = "test_session_step_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    test_session_step_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_session_steps.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    teacher_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("uploaded_audios.id", ondelete="SET NULL"),
        nullable=True,
    )
    teacher_image_ids: Mapped[list[str]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
        default=list,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    step: Mapped[TestSessionStep] = relationship("TestSessionStep")
    teacher_voice: Mapped[UploadedAudio | None] = relationship("UploadedAudio")


class HomeworkSubmissionFeedback(Base):
    __tablename__ = "homework_submission_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    homework_submission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("homework_submissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    teacher_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_voice_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("uploaded_audios.id", ondelete="SET NULL"),
        nullable=True,
    )
    teacher_image_ids: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
        default=list,
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    submission: Mapped[HomeworkSubmission] = relationship("HomeworkSubmission")
    teacher_voice: Mapped[UploadedAudio | None] = relationship("UploadedAudio")
