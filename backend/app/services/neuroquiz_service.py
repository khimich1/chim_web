"""Neuroquiz business logic: ensure cache, session, answer, skip, vote."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    NeuroQuizQuestion,
    NeuroQuizQuestionStatus,
    NeuroQuizVoteValue,
    User,
)
from app.models.enums import ActivityEventType
from app.repositories.app.neuroquiz_repo import NeuroQuizRepository
from app.repositories.content.lectures import LectureContentRepo
from app.schemas.neuroquiz import (
    NeuroQuizOption,
    NeuroQuizQuestionPublic,
    NeuroQuizSession,
    NeuroQuizSubmitResult,
)
from app.services.activity_service import ActivityService
from app.services.neuroquiz_generate import (
    MockNeuroQuizGenerator,
    NeuroQuizGenerator,
    explanation_has_current_generation,
    load_chunk_context,
    options_have_generic_junk,
    options_reuse_sibling_answers,
    strip_generation_marker,
)

POINTS_NEUROQUIZ_CORRECT = 1
TARGET_ACTIVE_QUESTIONS = 4

# Per-process locks so concurrent warmup/GET for the same chunk cannot double-insert.
_ensure_locks: dict[tuple[str, int], asyncio.Lock] = {}
_ensure_locks_guard = asyncio.Lock()


async def _ensure_lock_for(topic: str, chunk_idx: int) -> asyncio.Lock:
    async with _ensure_locks_guard:
        key = (topic, chunk_idx)
        lock = _ensure_locks.get(key)
        if lock is None:
            lock = asyncio.Lock()
            _ensure_locks[key] = lock
        return lock


class NeuroQuizService:
    def __init__(
        self,
        session: AsyncSession,
        lectures: LectureContentRepo,
        *,
        generator: NeuroQuizGenerator | None = None,
        activity: ActivityService | None = None,
    ) -> None:
        self._session = session
        self._lectures = lectures
        self._repo = NeuroQuizRepository(session)
        self._generator = generator or MockNeuroQuizGenerator()
        self._activity = activity or ActivityService(session)

    async def ensure_questions(self, topic: str, chunk_idx: int) -> list[NeuroQuizQuestion]:
        context = load_chunk_context(self._lectures, topic, chunk_idx)
        if context is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found",
            )
        lecture, qa_pairs = context
        resolved = self._lectures.resolve_topic_name(topic) or topic

        lock = await _ensure_lock_for(resolved, chunk_idx)
        async with lock:
            return await self._ensure_questions_locked(
                resolved,
                chunk_idx,
                lecture=lecture,
                qa_pairs=qa_pairs,
            )

    async def _ensure_questions_locked(
        self,
        resolved: str,
        chunk_idx: int,
        *,
        lecture: str,
        qa_pairs: list[Any],
    ) -> list[NeuroQuizQuestion]:
        active = await self._repo.list_active_questions(resolved, chunk_idx)
        # Retire stale/low-quality cache so improved generators refill on warmup/GET:
        # - generic filler distractors
        # - outdated generation version (prompt/rules bump)
        # - distractors that reuse other QA answers from this chunk (sibling-true bug)
        sibling_answers = [p.answer.strip() for p in qa_pairs if p.answer.strip()]
        retired_junk = False
        for question in active:
            should_retire = False
            if options_have_generic_junk(question.options_json):
                should_retire = True
            elif not explanation_has_current_generation(question.explanation):
                should_retire = True
            elif options_reuse_sibling_answers(
                question.options_json,
                correct_option_id=question.correct_option_id,
                sibling_answers=sibling_answers,
            ):
                should_retire = True
            if should_retire:
                await self._repo.retire_question(question)
                retired_junk = True
        if retired_junk:
            await self._session.commit()
            active = await self._repo.list_active_questions(resolved, chunk_idx)

        need = TARGET_ACTIVE_QUESTIONS - len(active)
        if need <= 0:
            return active[:TARGET_ACTIVE_QUESTIONS]

        # Re-check inside the lock after any await gap (generation is sync/blocking).
        generated = await asyncio.to_thread(
            self._generator.generate_for_chunk,
            topic=resolved,
            chunk_idx=chunk_idx,
            lecture=lecture,
            qa_pairs=qa_pairs,
            need=need,
        )
        # Another waiter may have filled the pool while we generated.
        active = await self._repo.list_active_questions(resolved, chunk_idx)
        need = TARGET_ACTIVE_QUESTIONS - len(active)
        if need <= 0:
            return active[:TARGET_ACTIVE_QUESTIONS]

        start_pos = len(active)
        new_rows: list[NeuroQuizQuestion] = []
        for offset, item in enumerate(generated[:need]):
            new_rows.append(
                NeuroQuizQuestion(
                    topic=resolved,
                    chunk_idx=chunk_idx,
                    position=start_pos + offset,
                    prompt=item.prompt,
                    options_json=list(item.options),
                    correct_option_id=item.correct_option_id,
                    explanation=item.explanation,
                    source=item.source,
                    status=NeuroQuizQuestionStatus.ACTIVE,
                )
            )
        if new_rows:
            await self._repo.add_questions(new_rows)
            await self._session.commit()
        return await self._repo.list_active_questions(resolved, chunk_idx)

    async def warmup(self, topic: str, chunk_idx: int) -> None:
        await self.ensure_questions(topic, chunk_idx)

    async def get_session(
        self,
        student: User,
        topic: str,
        chunk_idx: int,
    ) -> NeuroQuizSession:
        resolved = self._lectures.resolve_topic_name(topic) or topic
        questions = await self.ensure_questions(resolved, chunk_idx)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neuroquiz questions unavailable",
            )
        scoring_enabled = not await self._repo.has_completed_attempt(
            student.id,
            resolved,
            chunk_idx,
        )
        open_attempt = await self._repo.get_open_attempt(
            student.id,
            resolved,
            chunk_idx,
        )
        answered: set[str] = set()
        if open_attempt is not None:
            answered = {str(x) for x in (open_attempt.answered_question_ids or [])}

        # Open pass: omit already-answered so client index 0 is always answerable.
        remaining = [q for q in questions if str(q.id) not in answered]
        pool = remaining if open_attempt is not None else list(questions)
        if not pool:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Neuroquiz questions unavailable",
            )

        public = [
            NeuroQuizQuestionPublic(
                id=q.id,
                prompt=q.prompt,
                options=[NeuroQuizOption.model_validate(opt) for opt in q.options_json],
            )
            for q in pool[:TARGET_ACTIVE_QUESTIONS]
        ]
        return NeuroQuizSession(
            topic=resolved,
            chunk_idx=chunk_idx,
            scoring_enabled=scoring_enabled,
            questions=public,
        )

    async def submit_answer(
        self,
        student: User,
        topic: str,
        chunk_idx: int,
        question_id: uuid.UUID,
        option_id: str,
    ) -> NeuroQuizSubmitResult:
        resolved = self._lectures.resolve_topic_name(topic) or topic
        question = await self._repo.get_question(question_id)
        if (
            question is None
            or question.topic != resolved
            or question.chunk_idx != chunk_idx
            or question.status != NeuroQuizQuestionStatus.ACTIVE
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        option_ids = {opt.get("id") for opt in question.options_json}
        if option_id not in option_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid option_id",
            )

        scoring_enabled = not await self._repo.has_completed_attempt(
            student.id,
            resolved,
            chunk_idx,
        )

        active = await self._repo.list_active_questions(resolved, chunk_idx)
        pass_ids = [str(q.id) for q in active[:TARGET_ACTIVE_QUESTIONS]]
        if str(question.id) not in pass_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not in current quiz",
            )

        attempt = await self._repo.get_open_attempt(student.id, resolved, chunk_idx)
        if attempt is None:
            attempt = await self._repo.create_attempt(
                student.id,
                resolved,
                chunk_idx,
                pass_question_ids=pass_ids,
            )
        elif not attempt.pass_question_ids:
            attempt.pass_question_ids = pass_ids

        answered = list(attempt.answered_question_ids or [])
        qid = str(question.id)
        if qid in answered:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Question already answered in this pass",
            )

        correct = option_id == question.correct_option_id
        points_awarded = 0
        if correct and scoring_enabled:
            # Cap: at most TARGET points per chunk (dislike-farm cannot exceed).
            already = len(answered)
            if already < TARGET_ACTIVE_QUESTIONS:
                result = await self._activity.record_event(
                    student.id,
                    ActivityEventType.NEUROQUIZ_CORRECT,
                    qid,
                    POINTS_NEUROQUIZ_CORRECT,
                    payload={"topic": resolved, "chunk_idx": chunk_idx},
                )
                points_awarded = result.points_awarded

        answered.append(qid)
        attempt.answered_question_ids = answered

        pass_set = {str(x) for x in (attempt.pass_question_ids or pass_ids)}
        # Complete when original pass is done OR student has answered TARGET questions
        # (blocks dislike-farm from leaving scoring unlocked forever).
        quiz_completed = pass_set.issubset(set(answered)) or (
            len(answered) >= TARGET_ACTIVE_QUESTIONS
        )
        if quiz_completed:
            await self._repo.mark_attempt_completed(attempt)

        await self._session.commit()
        return NeuroQuizSubmitResult(
            correct=correct,
            correct_option_id=question.correct_option_id,
            explanation=strip_generation_marker(question.explanation),
            points_awarded=points_awarded,
            quiz_completed=quiz_completed,
        )

    async def skip(self, student: User, topic: str, chunk_idx: int) -> None:
        """Skip does not lock scoring — no completed write."""
        del student, topic, chunk_idx
        return None

    async def vote(
        self,
        student: User,
        question_id: uuid.UUID,
        value: NeuroQuizVoteValue,
    ) -> dict[str, Any]:
        question = await self._repo.get_question(question_id)
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )
        answered = await self._repo.student_has_answered_question(
            student.id,
            question_id,
            topic=question.topic,
            chunk_idx=question.chunk_idx,
        )
        if not answered:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Answer the question before voting",
            )
        await self._repo.upsert_vote(student.id, question_id, value)
        if value == NeuroQuizVoteValue.DISLIKE:
            await self._repo.retire_question(question)
            # Top up pool if below target
            await self.ensure_questions(question.topic, question.chunk_idx)
        else:
            await self._session.commit()
        return {"status": "ok"}
