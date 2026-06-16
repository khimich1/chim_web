"""Student profile ORM model (track + teacher link)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ExamTrack

if TYPE_CHECKING:
    from app.models.user import User


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track: Mapped[ExamTrack] = mapped_column(
        Enum(ExamTrack, name="exam_track", native_enum=False, length=10),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="student_profile",
        foreign_keys=[user_id],
    )
    teacher: Mapped[User] = relationship(
        "User",
        back_populates="students",
        foreign_keys=[teacher_id],
    )
