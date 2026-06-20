"""Student homework endpoints (SPEC §1.9.9)."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import StudentUser
from app.db.session import get_db
from app.schemas.homework_feedback import StudentHomeworkFeedbackRead
from app.services.homework_feedback_service import HomeworkFeedbackService

router = APIRouter(prefix="/api/student/homework", tags=["student-homework"])


@router.get("/{assignment_id}/feedback", response_model=StudentHomeworkFeedbackRead)
async def get_student_homework_feedback(
    assignment_id: uuid.UUID,
    student: StudentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentHomeworkFeedbackRead:
    return await HomeworkFeedbackService(db).get_student_feedback(
        student,
        assignment_id,
    )
