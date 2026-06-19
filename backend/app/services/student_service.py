"""Student management business logic (teacher-owned learners)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import User
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.user_repo import UserRepository
from app.schemas.students import StudentCreate, StudentRead
from app.services.onboarding_service import is_student_activated, resolve_students_activation


class StudentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._students = StudentRepository(session)
        self._users = UserRepository(session)

    async def list_students(self, teacher_id: uuid.UUID) -> list[StudentRead]:
        users = await self._students.list_by_teacher(teacher_id)
        profiles = [
            user.student_profile
            for user in users
            if user.student_profile is not None
        ]
        activation = await resolve_students_activation(self._session, profiles)
        return [
            _to_student_read(
                user,
                is_activated=activation.get(user.id, False),
            )
            for user in users
        ]

    async def create_student(
        self,
        teacher_id: uuid.UUID,
        data: StudentCreate,
    ) -> StudentRead:
        existing = await self._users.get_by_email(data.email)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = await self._students.create(
            email=data.email,
            password_hash=hash_password(data.password),
            teacher_id=teacher_id,
            track=data.track,
        )
        await self._session.commit()
        return _to_student_read(user, is_activated=False)


def _to_student_read(user: User, *, is_activated: bool | None = None) -> StudentRead:
    profile = user.student_profile
    if profile is None:
        raise ValueError("Student user is missing a profile")
    activated = (
        is_activated
        if is_activated is not None
        else is_student_activated(profile)
    )
    return StudentRead(
        id=user.id,
        email=user.email,
        track=profile.track,
        created_at=user.created_at,
        first_login_at=profile.first_login_at,
        onboarding_completed_at=profile.onboarding_completed_at,
        is_activated=activated,
    )
