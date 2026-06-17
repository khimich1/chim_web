"""Data access for student users and their profiles (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models import StudentProfile, User, UserRole
from app.models.enums import ExamTrack


class StudentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_teacher(self, teacher_id: uuid.UUID) -> list[User]:
        """Return student users owned by the given teacher, newest first."""
        stmt = (
            select(User)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(StudentProfile.teacher_id == teacher_id)
            .options(joinedload(User.student_profile))
            .order_by(User.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.unique().all())

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        teacher_id: uuid.UUID,
        track: ExamTrack,
    ) -> User:
        user = User(
            email=email,
            password_hash=password_hash,
            role=UserRole.STUDENT,
        )
        self._session.add(user)
        await self._session.flush()

        profile = StudentProfile(
            user_id=user.id,
            teacher_id=teacher_id,
            track=track,
        )
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(user, attribute_names=["student_profile", "created_at"])
        return user

    async def get_student_for_teacher(
        self,
        student_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> User | None:
        """Return a student user if owned by the given teacher."""
        stmt = (
            select(User)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .where(
                User.id == student_id,
                StudentProfile.teacher_id == teacher_id,
            )
            .options(joinedload(User.student_profile))
        )
        return await self._session.scalar(stmt)
