"""Students endpoints.

| Method | Path                         | Role    | Request           | Response              |
|--------|------------------------------|---------|-------------------|-----------------------|
| GET    | /api/students                | teacher | -                 | list[StudentRead]     |
| POST   | /api/students                | teacher | StudentCreate     | StudentRead (201)     |
| GET    | /api/students/me/stats       | student | -                 | StudentStatsRead      |
| GET    | /api/students/me/onboarding  | student | -                 | OnboardingRead        |
| GET    | /api/students/me/onboarding/welcome | student | -          | OnboardingWelcomeRead |
| PATCH  | /api/students/me/onboarding  | student | OnboardingPatch   | OnboardingRead        |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import StudentUser, TeacherUser, get_activity_service, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.activity import StudentStatsRead
from app.schemas.onboarding import OnboardingPatch, OnboardingRead, OnboardingWelcomeRead
from app.schemas.students import StudentCreate, StudentRead
from app.services.activity_service import ActivityService
from app.services.onboarding_service import OnboardingService
from app.services.student_service import StudentService

router = APIRouter(prefix="/api/students", tags=["students"])


def get_onboarding_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    activity: Annotated[ActivityService, Depends(get_activity_service)],
) -> OnboardingService:
    return OnboardingService(db, settings, activity)


@router.get("/me/stats", response_model=StudentStatsRead)
async def get_my_stats(
    student: StudentUser,
    activity: Annotated[ActivityService, Depends(get_activity_service)],
) -> StudentStatsRead:
    return await activity.get_stats(student.id)


@router.get("/me/onboarding", response_model=OnboardingRead)
async def get_my_onboarding(
    student: StudentUser,
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OnboardingRead:
    result = await onboarding.get_status(student)
    await db.commit()
    return result


@router.get("/me/onboarding/welcome", response_model=OnboardingWelcomeRead)
async def get_my_onboarding_welcome(
    student: StudentUser,
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OnboardingWelcomeRead:
    result = await onboarding.get_welcome(student)
    await db.commit()
    return result


@router.patch("/me/onboarding", response_model=OnboardingRead)
async def patch_my_onboarding(
    payload: OnboardingPatch,
    student: StudentUser,
    onboarding: Annotated[OnboardingService, Depends(get_onboarding_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OnboardingRead:
    result = await onboarding.patch(student, payload)
    await db.commit()
    return result


@router.get("", response_model=list[StudentRead])
async def list_students(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StudentRead]:
    return await StudentService(db).list_students(teacher.id)


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentRead:
    return await StudentService(db).create_student(teacher.id, payload)
