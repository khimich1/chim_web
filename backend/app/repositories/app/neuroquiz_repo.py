"""Data access for neuroquiz tables (app DB)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    NeuroQuizChunkAttempt,
    NeuroQuizQuestion,
    NeuroQuizQuestionStatus,
    NeuroQuizVote,
    NeuroQuizVoteValue,
    StudentActivityEvent,
)
from app.models.enums import ActivityEventType


class NeuroQuizRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_questions(
        self,
        topic: str,
        chunk_idx: int,
    ) -> list[NeuroQuizQuestion]:
        stmt = (
            select(NeuroQuizQuestion)
            .where(
                NeuroQuizQuestion.topic == topic,
                NeuroQuizQuestion.chunk_idx == chunk_idx,
                NeuroQuizQuestion.status == NeuroQuizQuestionStatus.ACTIVE,
            )
            .order_by(NeuroQuizQuestion.position.asc().nulls_last(), NeuroQuizQuestion.created_at.asc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count_active(self, topic: str, chunk_idx: int) -> int:
        return len(await self.list_active_questions(topic, chunk_idx))

    async def get_question(self, question_id: uuid.UUID) -> NeuroQuizQuestion | None:
        return await self._session.scalar(
            select(NeuroQuizQuestion).where(NeuroQuizQuestion.id == question_id)
        )

    async def add_questions(self, questions: list[NeuroQuizQuestion]) -> list[NeuroQuizQuestion]:
        self._session.add_all(questions)
        await self._session.flush()
        return questions

    async def has_completed_attempt(
        self,
        student_id: uuid.UUID,
        topic: str,
        chunk_idx: int,
    ) -> bool:
        stmt = (
            select(NeuroQuizChunkAttempt.id)
            .where(
                NeuroQuizChunkAttempt.student_id == student_id,
                NeuroQuizChunkAttempt.topic == topic,
                NeuroQuizChunkAttempt.chunk_idx == chunk_idx,
                NeuroQuizChunkAttempt.completed.is_(True),
            )
            .limit(1)
        )
        return await self._session.scalar(stmt) is not None

    async def get_open_attempt(
        self,
        student_id: uuid.UUID,
        topic: str,
        chunk_idx: int,
    ) -> NeuroQuizChunkAttempt | None:
        stmt = (
            select(NeuroQuizChunkAttempt)
            .where(
                NeuroQuizChunkAttempt.student_id == student_id,
                NeuroQuizChunkAttempt.topic == topic,
                NeuroQuizChunkAttempt.chunk_idx == chunk_idx,
                NeuroQuizChunkAttempt.completed.is_(False),
            )
            .order_by(NeuroQuizChunkAttempt.created_at.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def list_attempts_for_chunk(
        self,
        student_id: uuid.UUID,
        topic: str,
        chunk_idx: int,
    ) -> list[NeuroQuizChunkAttempt]:
        stmt = (
            select(NeuroQuizChunkAttempt)
            .where(
                NeuroQuizChunkAttempt.student_id == student_id,
                NeuroQuizChunkAttempt.topic == topic,
                NeuroQuizChunkAttempt.chunk_idx == chunk_idx,
            )
            .order_by(NeuroQuizChunkAttempt.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def student_has_answered_question(
        self,
        student_id: uuid.UUID,
        question_id: uuid.UUID,
        *,
        topic: str,
        chunk_idx: int,
    ) -> bool:
        qid = str(question_id)
        attempts = await self.list_attempts_for_chunk(student_id, topic, chunk_idx)
        for attempt in attempts:
            answered = attempt.answered_question_ids or []
            if qid in {str(x) for x in answered}:
                return True
        return False

    async def create_attempt(
        self,
        student_id: uuid.UUID,
        topic: str,
        chunk_idx: int,
        *,
        pass_question_ids: list[str] | None = None,
    ) -> NeuroQuizChunkAttempt:
        attempt = NeuroQuizChunkAttempt(
            student_id=student_id,
            topic=topic,
            chunk_idx=chunk_idx,
            completed=False,
            pass_question_ids=list(pass_question_ids or []),
            answered_question_ids=[],
        )
        self._session.add(attempt)
        await self._session.flush()
        return attempt

    async def mark_attempt_completed(self, attempt: NeuroQuizChunkAttempt) -> NeuroQuizChunkAttempt:
        attempt.completed = True
        attempt.completed_at = datetime.now(timezone.utc)
        await self._session.flush()
        return attempt

    async def upsert_vote(
        self,
        student_id: uuid.UUID,
        question_id: uuid.UUID,
        value: NeuroQuizVoteValue,
    ) -> NeuroQuizVote:
        existing = await self._session.get(
            NeuroQuizVote,
            {"student_id": student_id, "question_id": question_id},
        )
        if existing is None:
            vote = NeuroQuizVote(
                student_id=student_id,
                question_id=question_id,
                value=value,
            )
            self._session.add(vote)
            await self._session.flush()
            return vote
        existing.value = value
        await self._session.flush()
        return existing

    async def retire_question(self, question: NeuroQuizQuestion) -> NeuroQuizQuestion:
        question.status = NeuroQuizQuestionStatus.RETIRED
        await self._session.flush()
        return question

    async def count_neuroquiz_correct_for_chunk(
        self,
        student_id: uuid.UUID,
        topic: str,
        chunk_idx: int,
    ) -> int:
        """Count NEUROQUIZ_CORRECT ledger events for this student+topic+chunk."""
        stmt = select(StudentActivityEvent).where(
            StudentActivityEvent.student_id == student_id,
            StudentActivityEvent.event_type == ActivityEventType.NEUROQUIZ_CORRECT,
        )
        rows = (await self._session.scalars(stmt)).all()
        return sum(
            1
            for event in rows
            if event.payload.get("topic") == topic
            and event.payload.get("chunk_idx") == chunk_idx
        )

    async def student_has_answered_question(
        self,
        student_id: uuid.UUID,
        question_id: uuid.UUID,
        *,
        topic: str,
        chunk_idx: int,
    ) -> bool:
        """True if student answered this question in any attempt on the chunk."""
        stmt = select(NeuroQuizChunkAttempt).where(
            NeuroQuizChunkAttempt.student_id == student_id,
            NeuroQuizChunkAttempt.topic == topic,
            NeuroQuizChunkAttempt.chunk_idx == chunk_idx,
        )
        attempts = (await self._session.scalars(stmt)).all()
        qid = str(question_id)
        return any(qid in (attempt.answered_question_ids or []) for attempt in attempts)
