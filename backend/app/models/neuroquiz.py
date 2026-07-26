"""Neuroquiz ORM models: cached MCQ questions, chunk attempts, votes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
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
from app.models.enums import (
    NeuroQuizQuestionSource,
    NeuroQuizQuestionStatus,
    NeuroQuizVoteValue,
)

if TYPE_CHECKING:
    from app.models.user import User


class NeuroQuizQuestion(Base):
    __tablename__ = "neuroquiz_questions"
    __table_args__ = (
        Index("ix_neuroquiz_questions_topic_chunk_status", "topic", "chunk_idx", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
    )
    correct_option_id: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[NeuroQuizQuestionSource] = mapped_column(
        Enum(
            NeuroQuizQuestionSource,
            name="neuroquiz_question_source",
            native_enum=False,
            length=32,
        ),
        nullable=False,
    )
    status: Mapped[NeuroQuizQuestionStatus] = mapped_column(
        Enum(
            NeuroQuizQuestionStatus,
            name="neuroquiz_question_status",
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=NeuroQuizQuestionStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class NeuroQuizChunkAttempt(Base):
    __tablename__ = "neuroquiz_chunk_attempts"
    __table_args__ = (
        Index(
            "ix_neuroquiz_chunk_attempts_student_topic_chunk",
            "student_id",
            "topic",
            "chunk_idx",
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
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    chunk_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    # Pass tracking (needed for scoring lock after full quiz; not in original §8 sketch)
    pass_question_ids: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
        insert_default=list,
        default=list,
    )
    answered_question_ids: Mapped[list[Any]] = mapped_column(
        JSON().with_variant(SQLiteJSON, "sqlite"),
        nullable=False,
        insert_default=list,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped[User] = relationship("User")


class NeuroQuizVote(Base):
    __tablename__ = "neuroquiz_votes"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "question_id",
            name="uq_neuroquiz_vote_student_question",
        ),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("neuroquiz_questions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    value: Mapped[NeuroQuizVoteValue] = mapped_column(
        Enum(
            NeuroQuizVoteValue,
            name="neuroquiz_vote_value",
            native_enum=False,
            length=16,
        ),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    student: Mapped[User] = relationship("User")
    question: Mapped[NeuroQuizQuestion] = relationship("NeuroQuizQuestion")
