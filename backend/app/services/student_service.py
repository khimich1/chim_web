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


class StudentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._students = StudentRepository(session)
        self._users = UserRepository(session)

    async def list_students(self, teacher_id: uuid.UUID) -> list[StudentRead]:
        users = await self._students.list_by_teacher(teacher_id)
        return [_to_student_read(user) for user in users]

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
        return _to_student_read(user)


def _to_student_read(user: User) -> StudentRead:
    profile = user.student_profile
    if profile is None:
        raise ValueError("Student user is missing a profile")
    return StudentRead(
        id=user.id,
        email=user.email,
        track=profile.track,
        created_at=user.created_at,
    )
