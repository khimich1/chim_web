"""Exam (content DB) test session adapter — practice and exam steps in mixed sessions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models import (
    StepStatus,
    TestSession,
    TestSessionStatus,
    TestSessionStep,
    User,
)
from app.models.enums import TestSessionSource
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo, TestQuestion
from app.schemas.test_session import (
    SessionCreate,
    SessionRead,
    SessionSummary,
    SessionSummaryStep,
    StepAttachAnswerImageResponse,
    StepCheckResponse,
    StepCompareResponse,
    StepRead,
)
from app.services.content_grading import (
    exam_step_score_parts,
    get_content_grading_mode,
    step_grading_mode_for_exam,
)
from app.services.image_substitution import (
    reference_answer_blocks_from_correct_ans,
    substitute_image_placeholders,
)
from app.services.onboarding_service import OnboardingService
from app.services.test_session.common import (
    SessionAdapterBase,
    answer_image_url,
    session_duration_minutes,
)


class ExamSessionAdapter(SessionAdapterBase):
    """Practice sessions and exam-content steps (variant, types, partial)."""

    async def create_session(
        self,
        student: User,
        data: SessionCreate,
    ) -> SessionRead:
        track = await self.resolve_track(student)
        repo = self.content_repo(track)
        practice_task_type: int | None = None

        variant = (data.variant_ref or "").strip()
        if variant:
            sources = [(variant, data.types)]
            practice_task_type = None
            distinct_variants = {v for v, _ in sources}
            variant_ref = (
                next(iter(distinct_variants)) if len(distinct_variants) == 1 else None
            )
        else:
            assert data.types is not None
            sources = repo.expand_types_across_variants(data.types, track=track)
            practice_task_type = data.types[0] if len(data.types) == 1 else None
            variant_ref = None

        questions = self.collect_questions(repo, sources)
        if not questions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No questions found for the requested variant",
            )

        steps = [
            TestSessionStep(
                position=index,
                test_id=question.id,
                status=StepStatus.UNSEEN,
            )
            for index, question in enumerate(questions)
        ]

        test_session = TestSession(
            student_id=student.id,
            track=track,
            source=TestSessionSource.EXAM,
            variant_ref=variant_ref,
            practice_task_type=practice_task_type,
            status=TestSessionStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
            steps=steps,
        )
        await self._repo.add(test_session)
        await OnboardingService(self._session, self._settings).mark_first_action(
            student.id,
            action_type="test_session",
        )
        await self._session.commit()

        reloaded = await self._repo.get_with_steps(test_session.id)
        assert reloaded is not None
        return self.to_session_read(reloaded, repo)

    def collect_questions(
        self,
        repo: ExamContentRepo,
        sources: list[tuple[str, list[int] | None]],
    ) -> list[TestQuestion]:
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

    async def check_step(
        self,
        student: User,
        test_session: TestSession,
        position: int,
        answer: str,
    ) -> StepCheckResponse:
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        step = self.find_step(test_session, position)
        repo = self.content_repo(test_session.track)
        question = self.require_question(repo, self.require_step_test_id(step))

        if get_content_grading_mode(test_session.track, question.type) == "self_check":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Use compare for self_check steps",
            )

        was_already_correct = step.is_correct is True
        is_correct = self._grading.grade(answer, question.correct_ans)
        step.answer = answer
        step.is_correct = is_correct
        step.status = StepStatus.CHECKED
        step.checked_at = datetime.now(timezone.utc)
        await self._session.commit()

        if is_correct and not was_already_correct:
            step_id = step.id
            student_id = student.id
            await self.run_activity_hook(
                "record_step_correct",
                lambda: self._activity.record_step_correct(student_id, step_id),
            )

        return StepCheckResponse(
            position=step.position,
            is_correct=is_correct,
            status=step.status,
        )

    async def attach_answer_image(
        self,
        student: User,
        test_session: TestSession,
        step: TestSessionStep,
        answer_image_id: uuid.UUID,
    ) -> StepAttachAnswerImageResponse:
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        if test_session.homework_assignment_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Answer image upload is only required for homework sessions",
            )
        repo = self.content_repo(test_session.track)
        question = self.require_question(repo, self.require_step_test_id(step))
        if get_content_grading_mode(test_session.track, question.type) != "self_check":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Answer image is only for self_check steps",
            )
        if step.status == StepStatus.CHECKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot replace photo after compare",
            )

        image = await self._upload_repo.get_by_id(answer_image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        if image.owner_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not your image",
            )

        step.answer_image_id = answer_image_id
        await self._session.commit()

        return StepAttachAnswerImageResponse(
            position=step.position,
            answer_image_id=answer_image_id,
            answer_image_url=answer_image_url(answer_image_id),
        )

    async def compare_step(
        self,
        student: User,
        test_session: TestSession,
        step: TestSessionStep,
        answer: str,
    ) -> StepCompareResponse:
        if test_session.status == TestSessionStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already completed",
            )
        repo = self.content_repo(test_session.track)
        question = self.require_question(repo, self.require_step_test_id(step))
        if get_content_grading_mode(test_session.track, question.type) != "self_check":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Use check for exact steps",
            )
        reference_answer = reference_answer_blocks_from_correct_ans(question.correct_ans)
        if not reference_answer:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Question has no reference answer",
            )
        if step.status == StepStatus.CHECKED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Step already checked",
            )
        if test_session.homework_assignment_id is not None and step.answer_image_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Answer image is required for self_check homework steps",
            )

        step.answer = answer
        step.status = StepStatus.CHECKED
        step.checked_at = datetime.now(timezone.utc)
        await self._session.commit()

        return StepCompareResponse(
            position=step.position,
            status=step.status,
            reference_answer=reference_answer,
        )

    async def complete_session(
        self,
        student: User,
        test_session: TestSession,
    ) -> SessionSummary:
        score = 0
        max_score = 0
        repo = self.content_repo(test_session.track)
        for step in test_session.steps:
            question = self.require_question(repo, self.require_step_test_id(step))
            step_max, step_score = exam_step_score_parts(
                test_session.track, question.type, step
            )
            max_score += step_max
            score += step_score

        was_already_completed = test_session.status == TestSessionStatus.COMPLETED
        completed_at = datetime.now(timezone.utc)
        if not was_already_completed:
            test_session.status = TestSessionStatus.COMPLETED
            test_session.completed_at = completed_at
        test_session.score = score
        test_session.max_score = max_score
        await self._session.commit()

        if not was_already_completed:
            minutes = session_duration_minutes(test_session.created_at, completed_at)
            student_id = student.id
            await self.run_activity_hook(
                "add_session_minutes",
                lambda: self._activity.add_session_minutes(student_id, minutes),
            )

        summary_steps = [
            SessionSummaryStep(
                position=step.position,
                test_id=step.test_id,
                type=self.require_question(
                    repo, self.require_step_test_id(step)
                ).type,
                grading_mode=step_grading_mode_for_exam(
                    test_session.track,
                    self.require_question(
                        repo, self.require_step_test_id(step)
                    ).type,
                ),
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

    def to_session_read(
        self, test_session: TestSession, repo: ExamContentRepo
    ) -> SessionRead:
        steps: list[StepRead] = []
        for step in test_session.steps:
            question = self.require_question(repo, self.require_step_test_id(step))
            steps.append(
                StepRead(
                    position=step.position,
                    test_id=step.test_id,
                    type=question.type,
                    question=substitute_image_placeholders(question.question),
                    options=question.options,
                    grading_mode=step_grading_mode_for_exam(
                        test_session.track, question.type
                    ),
                    status=step.status,
                    answer=step.answer,
                    answer_image_id=step.answer_image_id,
                    answer_image_url=answer_image_url(step.answer_image_id),
                    is_correct=step.is_correct,
                    hint_used=step.hint_used,
                )
            )
        return SessionRead(
            id=test_session.id,
            track=test_session.track,
            source=test_session.source,
            variant_ref=test_session.variant_ref,
            homework_assignment_id=test_session.homework_assignment_id,
            custom_theme_id=test_session.custom_theme_id,
            status=test_session.status,
            score=test_session.score,
            max_score=test_session.max_score,
            total_steps=len(steps),
            created_at=test_session.created_at,
            steps=steps,
        )

    def exam_step_read(
        self,
        test_session: TestSession,
        step: TestSessionStep,
        repo: ExamContentRepo,
    ) -> StepRead:
        question = self.require_question(repo, self.require_step_test_id(step))
        return StepRead(
            position=step.position,
            test_id=step.test_id,
            type=question.type,
            question=substitute_image_placeholders(question.question),
            options=question.options,
            grading_mode=step_grading_mode_for_exam(test_session.track, question.type),
            status=step.status,
            answer=step.answer,
            answer_image_id=step.answer_image_id,
            answer_image_url=answer_image_url(step.answer_image_id),
            is_correct=step.is_correct,
            hint_used=step.hint_used,
        )

    def exam_summary_step(
        self,
        test_session: TestSession,
        step: TestSessionStep,
        repo: ExamContentRepo,
    ) -> SessionSummaryStep:
        question = self.require_question(repo, self.require_step_test_id(step))
        return SessionSummaryStep(
            position=step.position,
            test_id=step.test_id,
            type=question.type,
            grading_mode=step_grading_mode_for_exam(test_session.track, question.type),
            is_correct=step.is_correct,
            hint_used=step.hint_used,
        )

    def exam_step_score(
        self,
        test_session: TestSession,
        step: TestSessionStep,
        repo: ExamContentRepo,
    ) -> tuple[int, int]:
        question = self.require_question(repo, self.require_step_test_id(step))
        return exam_step_score_parts(test_session.track, question.type, step)

    @staticmethod
    def require_step_test_id(step: TestSessionStep) -> int:
        if step.test_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Step has no exam test content",
            )
        return step.test_id

    def require_question(
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
