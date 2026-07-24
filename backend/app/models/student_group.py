"""Student group ORM models (teacher-owned groups, ≤1 group per student)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class StudentGroup(Base):
    __tablename__ = "student_groups"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    teacher: Mapped[User] = relationship("User", foreign_keys=[teacher_id])
    members: Mapped[list[StudentGroupMember]] = relationship(
        "StudentGroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class StudentGroupMember(Base):
    __tablename__ = "student_group_members"
    __table_args__ = (
        UniqueConstraint(
            "student_user_id",
            name="uq_student_group_members_student_user_id",
        ),
        UniqueConstraint(
            "group_id",
            "student_user_id",
            name="uq_student_group_members_group_student",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("student_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group: Mapped[StudentGroup] = relationship(
        "StudentGroup",
        back_populates="members",
    )
    student: Mapped[User] = relationship("User", foreign_keys=[student_user_id])
