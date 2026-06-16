"""Authentication business logic: credential checks and student track lookup."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models import ExamTrack, StudentProfile, User, UserRole
from app.repositories.app.user_repo import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._users = UserRepository(session)

    async def authenticate(self, email: str, password: str) -> User | None:
        """Return the user if credentials are valid and the account is active."""
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    async def get_user_track(self, user: User) -> ExamTrack | None:
        """Exam track for students; None for teachers."""
        if user.role != UserRole.STUDENT:
            return None
        profile = await self._session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == user.id)
        )
        return profile.track if profile is not None else None
