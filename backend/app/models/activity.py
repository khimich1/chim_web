"""Student activity ledger and stats ORM models (Phase 13, SPEC §1.8).

``StudentActivityEvent`` is append-only; idempotency is enforced by
``UNIQUE (student_id, event_type, ref_id)``.

``ref_id`` stores opaque string keys: UUID of ``TestSessionStep`` /
``HomeworkAssignment`` as text, or calendar keys for streak bonuses
(``YYYY-MM-DD``, ``YYYY-Www``).
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Date,
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
from app.models.enums import ActivityEventType

if TYPE_CHECKING:
    from app.models.user import User


class StudentActivityEvent(Base):
    __tablename__ = "student_activity_events"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "event_type",
            "ref_id",
            name="uq_activity_event_student_type_ref",
        ),
    )

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
    event_type: Mapped[ActivityEventType] = mapped_column(
        Enum(
            ActivityEventType,
            name="activity_event_type",
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    ref_id: Mapped[str] = mapped_column(String(64), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
        insert_default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped[User] = relationship("User")


class StudentStats(Base):
    __tablename__ = "student_stats"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    total_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    week_points: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    current_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    longest_streak: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    last_active_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    tasks_solved: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    total_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    student: Mapped[User] = relationship("User")
