"""Student management business logic (teacher-owned learners)."""

from __future__ import annotations

import secrets
import string
import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import MIN_PASSWORD_LENGTH, hash_password
from app.models import User, UserRole
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.user_repo import UserRepository
from app.schemas.students import (
    StudentCreate,
    StudentPasswordResetRead,
    StudentRead,
)
from app.services.onboarding_service import is_student_activated, resolve_students_activation

_TEMP_PASSWORD_ALPHABET = string.ascii_letters + string.digits
_TEMP_PASSWORD_LENGTH = 10


def generate_temporary_password() -> str:
    """Random temp password for reset-password (shown once to the teacher)."""
    return "".join(
        secrets.choice(_TEMP_PASSWORD_ALPHABET)
        for _ in range(max(_TEMP_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH))
    )


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
            if (
                existing.role == UserRole.STUDENT
                and not existing.is_active
            ):
                owned = await self._students.get_by_email_for_teacher(
                    data.email,
                    teacher_id,
                )
                if owned is not None and owned.id == existing.id:
                    return await self._revive_student(owned, data)

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Login already registered",
            )

        user = await self._students.create(
            email=data.email,
            password_hash=hash_password(data.password),
            teacher_id=teacher_id,
            track=data.track,
        )
        await self._session.commit()
        return _to_student_read(user, is_activated=False)

    async def soft_delete_student(
        self,
        teacher_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> None:
        student = await self._students.get_student_for_teacher(
            student_id,
            teacher_id,
            active_only=True,
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )
        student.is_active = False
        await self._session.commit()

    async def reset_password(
        self,
        teacher_id: uuid.UUID,
        student_id: uuid.UUID,
    ) -> StudentPasswordResetRead:
        student = await self._students.get_student_for_teacher(
            student_id,
            teacher_id,
            active_only=True,
        )
        if student is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found",
            )
        temporary_password = generate_temporary_password()
        student.password_hash = hash_password(temporary_password)
        await self._session.commit()
        return StudentPasswordResetRead(temporary_password=temporary_password)

    async def _revive_student(
        self,
        student: User,
        data: StudentCreate,
    ) -> StudentRead:
        student.is_active = True
        student.password_hash = hash_password(data.password)
        profile = student.student_profile
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student profile not found",
            )
        profile.track = data.track
        await self._session.flush()
        await self._session.refresh(student, attribute_names=["student_profile", "created_at"])
        await self._session.commit()
        return _to_student_read(student, is_activated=False)


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
