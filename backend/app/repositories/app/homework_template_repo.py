"""Data access for homework templates (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import HomeworkTemplate


class HomeworkTemplateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_teacher(self, teacher_id: uuid.UUID) -> list[HomeworkTemplate]:
        stmt = (
            select(HomeworkTemplate)
            .where(HomeworkTemplate.teacher_id == teacher_id)
            .order_by(HomeworkTemplate.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_for_teacher(
        self,
        template_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> HomeworkTemplate | None:
        stmt = select(HomeworkTemplate).where(
            HomeworkTemplate.id == template_id,
            HomeworkTemplate.teacher_id == teacher_id,
        )
        return await self._session.scalar(stmt)

    async def add(self, template: HomeworkTemplate) -> HomeworkTemplate:
        self._session.add(template)
        await self._session.flush()
        await self._session.refresh(template)
        return template

    async def delete(self, template: HomeworkTemplate) -> None:
        await self._session.delete(template)
