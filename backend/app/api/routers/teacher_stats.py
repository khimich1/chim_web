"""Teacher-facing student activity stats (Phase 13, Task 62).

| Method | Path                         | Role    | Response                      |
|--------|------------------------------|---------|-------------------------------|
| GET    | /api/teacher/students/stats  | teacher | list[TeacherStudentStatsRead] |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import TeacherUser, get_activity_service
from app.schemas.activity import TeacherStudentStatsRead
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/api/teacher/students", tags=["teacher-stats"])


@router.get("/stats", response_model=list[TeacherStudentStatsRead])
async def list_teacher_students_stats(
    teacher: TeacherUser,
    activity: Annotated[ActivityService, Depends(get_activity_service)],
) -> list[TeacherStudentStatsRead]:
    return await activity.get_teacher_students_stats(teacher.id)
