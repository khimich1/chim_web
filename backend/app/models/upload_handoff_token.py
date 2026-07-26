"""UploadHandoffToken ORM model — QR mobile capture handoff (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.homework import HomeworkAssignment
    from app.models.test_session import TestSession
    from app.models.uploaded_image import UploadedImage
    from app.models.user import User


class UploadHandoffToken(Base):
    __tablename__ = "upload_handoff_tokens"
    __table_args__ = (
        CheckConstraint(
            "(purpose = 'answer' AND session_id IS NOT NULL AND student_id IS NOT NULL "
            "AND position IS NOT NULL AND homework_id IS NULL AND teacher_id IS NULL) OR "
            "(purpose = 'feedback' AND homework_id IS NOT NULL AND teacher_id IS NOT NULL "
            "AND session_id IS NULL AND student_id IS NULL)",
            name="ck_upload_handoff_purpose_fks",
        ),
    )

    token: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    purpose: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="answer",
        server_default="answer",
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("test_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    homework_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("homework_assignments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    staged_image_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("uploaded_images.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped[TestSession | None] = relationship(
        "TestSession",
        foreign_keys=[session_id],
    )
    student: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[student_id],
    )
    homework: Mapped[HomeworkAssignment | None] = relationship(
        "HomeworkAssignment",
        foreign_keys=[homework_id],
    )
    teacher: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[teacher_id],
    )
    staged_image: Mapped[UploadedImage | None] = relationship(
        "UploadedImage",
        foreign_keys=[staged_image_id],
    )
