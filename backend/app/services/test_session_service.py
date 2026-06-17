"""Stepik-style test session business logic.

Sessions live in the app DB; question content (text, correct answer, hint,
explanation) comes from the read-only content DB. `correct_ans` is never
returned to the client — only a boolean correctness result.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import (
    ExamTrack,
    HomeworkStatus,
    StepStatus,
    StudentProfile,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
    User,
)
from app.models.enums import HomeworkItemKind
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.test_session_repo import TestSessionRepository
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo, TestQuestion
from app.schemas.test_session import (
    ActiveSessionResponse,
    HintResponse,
    SessionCreate,
    SessionRead,
    SessionSummary,
    SessionSummaryStep,
    StepCheckResponse,
    StepRead,
)
from app.services.grading_service import GradingService
from app.services.image_substitution import substitute_image_placeholders


class TestSessionService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._repo = TestSessionRepository(session)
        self._grading = GradingService()
        self._content_repos = {
            ExamTrack.EGE: ExamContentRepo(settings.content_ege_db_path),
            ExamTrack.OGE: ExamContentRepo(settings.content_oge_db_path),
        }

    async def _resolve_track(self, student: User) -> ExamTrack:
        profile = await self._session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student.id)
        )
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        return profile.track

    def _content_repo(self, track: ExamTrack) -> ExamContentRepo:
        return self._content_repos[track]

    async def create_session(
        self, student: User, data: SessionCreate
    ) -> SessionRead:
        track = await self._resolve_track(student)
        repo = self._content_repo(track)

        if data.homework_assignment_id is not None:
            # Server is the source of truth for homework test scope: aggregate
            # every test item (possibly across variants) into one session.
            sources = await self._resolve_homework_sources(
                student, data.homework_assignment_id
            )
        else:
            assert data.variant_ref is not None  # enforced by SessionCreate validator
            sources = [(data.variant_ref, data.types)]

        questions = self._collect_questions(repo, sources)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found for the requested variant",
            )

        distinct_variants = {variant for variant, _ in sources}
        variant_ref = (
            next(iter(distinct_variants)) if len(distinct_variants) == 1 else None
        )

        test_session = TestSession(
            student_id=student.id,
            track=track,
            variant_ref=variant_ref,
            homework_assignment_id=data.homework_assignment_id,
            status=TestSessionStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
            steps=[
                TestSessionStep(
                    position=index,
                    test_id=question.id,
                    status=StepStatus.UNSEEN,
                )
                for index, question in enumerate(questions)
            ],
        )
        await self._repo.add(test_session)
        await self._session.commit()

        reloaded = await self._repo.get_with_steps(test_session.id)
        assert reloaded is not None
        return self._to_session_read(reloaded, repo)

    def _collect_questions(
        self,
        repo: ExamContentRepo,
        sources: list[tuple[str, list[int] | None]],
    ) -> list[TestQuestion]:
        """Gather (deduplicated) questions for one or more (variant, types) specs."""
        questions: list[TestQuestion] = []
        seen_ids: set[int] = set()
        for variant, types in sources:
            try:
                variant_questions = repo.list_questions(variant)
            except ContentDbError as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Test content database unavailable",
                ) from exc
            if types is not None:
                wanted = set(types)
                variant_questions = [q for q in variant_questions if q.type in wanted]
            for question in variant_questions:
                if question.id in seen_ids:
                    continue
                seen_ids.add(question.id)
                questions.append(question)
        return questions

    async def _resolve_homework_sources(
        self,
        student: User,
        homework_assignment_id: uuid.UUID,
    ) -> list[tuple[str, list[int] | None]]:
        assignment = await HomeworkRepository(self._session).get_by_id(
            homework_assignment_id
        )
        if assignment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework not found",
            )
        if assignment.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your homework assignment",
            )
        if assignment.status == HomeworkStatus.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Homework already submitted",
            )

        track = await self._resolve_track(student)
        repo = self._content_repo(track)
        sources: list[tuple[str, list[int] | None]] = []
        for item in assignment.items:
            kind = item.get("kind")
            if kind == HomeworkItemKind.TEST_VARIANT.value:
                sources.append((item["variant"], None))
            elif kind == HomeworkItemKind.TEST_PARTIAL.value:
                sources.append((item["variant"], list(item["types"])))
            elif kind == HomeworkItemKind.TEST_BY_TYPE.value:
                sources.extend(
                    repo.expand_types_across_variants(
                        list(item["types"]),
                        track=track,
                    )
                )

        if not sources:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Homework assignment has no test items",
            )
        return sources

    async def get_active_session(
        self,
        student: User,
        *,
        variant_ref: str | None = None,
        homework_assignment_id: uuid.UUID | None = None,
    ) -> ActiveSessionResponse:
        has_variant = bool((variant_ref or "").strip())
        has_homework = homework_assignment_id is not None
        if has_variant == has_homework:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide exactly one of variant_ref or homework_assignment_id",
            )

        if homework_assignment_id is not None:
            assignment = await HomeworkRepository(self._session).get_by_id(
                homework_assignment_id
            )
            if assignment is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Homework not found",
                )
            if assignment.student_id != student.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not your homework assignment",
                )

        active = await self._repo.find_latest_active(
            student.id,
            variant_ref=variant_ref.strip() if has_variant else None,
            homework_assignment_id=homework_assignment_id,
        )
        return ActiveSessionResponse(
            session_id=active.id if active is not None else None,
        )

    async def get_session(
        self, student: User, session_id: uuid.UUID
    ) -> SessionRead:
        test_session = await self._load_owned_session(student, session_id)
        repo = self._content_repo(test_session.track)
        return self._to_session_read(test_session, repo)

    async def check_step(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
        answer: str,
    ) -> StepCheckResponse:
        test_session = await self._load_owned_session(student, session_id)
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        step = self._find_step(test_session, position)
        repo = self._content_repo(test_session.track)
        question = self._require_question(repo, step.test_id)

        is_correct = self._grading.grade(answer, question.correct_ans)
        step.answer = answer
        step.is_correct = is_correct
        step.status = StepStatus.CHECKED
        step.checked_at = datetime.now(timezone.utc)
        await self._session.commit()

        return StepCheckResponse(
            position=step.position,
            is_correct=is_correct,
            status=step.status,
            detailed_explanation=question.detailed_explanation,
        )

    async def get_hint(
        self,
        student: User,
        session_id: uuid.UUID,
        position: int,
    ) -> HintResponse:
        test_session = await self._load_owned_session(student, session_id)
        step = self._find_step(test_session, position)
        repo = self._content_repo(test_session.track)
        question = self._require_question(repo, step.test_id)

        step.hint_used = True
        if step.status == StepStatus.UNSEEN:
            step.status = StepStatus.ANSWERED
        await self._session.commit()

        return HintResponse(hint=question.hint)

    async def complete_session(
        self, student: User, session_id: uuid.UUID
    ) -> SessionSummary:
        test_session = await self._load_owned_session(student, session_id)

        score = sum(1 for step in test_session.steps if step.is_correct)
        max_score = len(test_session.steps)

        if test_session.status != TestSessionStatus.COMPLETED:
            test_session.status = TestSessionStatus.COMPLETED
            test_session.completed_at = datetime.now(timezone.utc)
        test_session.score = score
        test_session.max_score = max_score
        await self._session.commit()

        repo = self._content_repo(test_session.track)
        summary_steps = [
            SessionSummaryStep(
                position=step.position,
                test_id=step.test_id,
                type=self._require_question(repo, step.test_id).type,
                is_correct=step.is_correct,
                hint_used=step.hint_used,
            )
            for step in test_session.steps
        ]
        return SessionSummary(
            id=test_session.id,
            status=test_session.status,
            score=score,
            max_score=max_score,
            completed_at=test_session.completed_at,
            steps=summary_steps,
        )

    async def _load_owned_session(
        self, student: User, session_id: uuid.UUID
    ) -> TestSession:
        test_session = await self._repo.get_with_steps(session_id)
        if test_session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found",
            )
        if test_session.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your session",
            )
        return test_session

    @staticmethod
    def _find_step(test_session: TestSession, position: int) -> TestSessionStep:
        for step in test_session.steps:
            if step.position == position:
                return step
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    def _require_question(
        self, repo: ExamContentRepo, test_id: int
    ) -> TestQuestion:
        try:
            question = repo.get_question(test_id)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test content database unavailable",
            ) from exc
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question content not found",
            )
        return question

    def _to_session_read(
        self, test_session: TestSession, repo: ExamContentRepo
    ) -> SessionRead:
        steps: list[StepRead] = []
        for step in test_session.steps:
            question = self._require_question(repo, step.test_id)
            hint = question.hint if step.hint_used else None
            explanation = None
            if step.status == StepStatus.CHECKED:
                explanation = question.detailed_explanation
            steps.append(
                StepRead(
                    position=step.position,
                    test_id=step.test_id,
                    type=question.type,
                    question=substitute_image_placeholders(question.question),
                    options=question.options,
                    status=step.status,
                    answer=step.answer,
                    is_correct=step.is_correct,
                    hint_used=step.hint_used,
                    hint=hint,
                    detailed_explanation=explanation,
                )
            )
        return SessionRead(
            id=test_session.id,
            track=test_session.track,
            variant_ref=test_session.variant_ref,
            homework_assignment_id=test_session.homework_assignment_id,
            status=test_session.status,
            score=test_session.score,
            max_score=test_session.max_score,
            total_steps=len(steps),
            steps=steps,
        )
