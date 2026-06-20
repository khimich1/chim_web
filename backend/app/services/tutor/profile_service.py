"""Tutor user profile persistence in PostgreSQL (Task 47, A7)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.app.tutor_repo import TutorRepository


class TutorProfileService:
    def __init__(self, db: AsyncSession, *, user_id: uuid.UUID) -> None:
        self._repo = TutorRepository(db)
        self._user_id = user_id

    async def load(self) -> dict[str, Any]:
        return await self._repo.get_profile_data(self._user_id)

    async def update_key(self, key: str, value: str) -> dict[str, Any]:
        return await self._repo.upsert_profile_key(self._user_id, key, value)
