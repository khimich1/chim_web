"""Data access for teacher themes and custom tasks (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import CustomTask, TeacherTheme


class TeacherThemeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_published_by_teacher(
        self,
        teacher_id: uuid.UUID,
    ) -> list[TeacherTheme]:
        stmt = (
            select(TeacherTheme)
            .where(
                TeacherTheme.teacher_id == teacher_id,
                TeacherTheme.is_published.is_(True),
            )
            .options(selectinload(TeacherTheme.tasks))
            .order_by(TeacherTheme.sort_order, TeacherTheme.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_published_for_student(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> TeacherTheme | None:
        stmt = (
            select(TeacherTheme)
            .where(
                TeacherTheme.id == theme_id,
                TeacherTheme.teacher_id == teacher_id,
                TeacherTheme.is_published.is_(True),
            )
            .options(selectinload(TeacherTheme.tasks))
        )
        return await self._session.scalar(stmt)

    async def count_tasks(self, theme_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(CustomTask).where(
            CustomTask.theme_id == theme_id
        )
        return int(await self._session.scalar(stmt) or 0)

    async def list_by_teacher(self, teacher_id: uuid.UUID) -> list[TeacherTheme]:
        stmt = (
            select(TeacherTheme)
            .where(TeacherTheme.teacher_id == teacher_id)
            .order_by(TeacherTheme.sort_order, TeacherTheme.created_at.desc())
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def list_by_teacher_with_task_counts(
        self,
        teacher_id: uuid.UUID,
    ) -> list[tuple[TeacherTheme, int]]:
        """List themes with aggregated task counts in a single query."""
        stmt = (
            select(
                TeacherTheme,
                func.count(CustomTask.id).label("task_count"),
            )
            .outerjoin(CustomTask, CustomTask.theme_id == TeacherTheme.id)
            .where(TeacherTheme.teacher_id == teacher_id)
            .group_by(TeacherTheme.id)
            .order_by(TeacherTheme.sort_order, TeacherTheme.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [(theme, int(count)) for theme, count in result.all()]

    async def get_by_id(self, theme_id: uuid.UUID) -> TeacherTheme | None:
        return await self._session.get(TeacherTheme, theme_id)

    async def get_for_teacher(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> TeacherTheme | None:
        stmt = select(TeacherTheme).where(
            TeacherTheme.id == theme_id,
            TeacherTheme.teacher_id == teacher_id,
        )
        return await self._session.scalar(stmt)

    async def add_theme(self, theme: TeacherTheme) -> TeacherTheme:
        self._session.add(theme)
        await self._session.flush()
        await self._session.refresh(theme)
        return theme

    async def delete_theme(self, theme: TeacherTheme) -> None:
        await self._session.delete(theme)

    async def list_tasks(self, theme_id: uuid.UUID) -> list[CustomTask]:
        stmt = (
            select(CustomTask)
            .where(CustomTask.theme_id == theme_id)
            .order_by(CustomTask.sort_order, CustomTask.created_at)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_task_by_id(self, task_id: uuid.UUID) -> CustomTask | None:
        stmt = (
            select(CustomTask)
            .where(CustomTask.id == task_id)
            .options(joinedload(CustomTask.theme))
        )
        return await self._session.scalar(stmt)

    async def get_task_for_teacher(
        self,
        task_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> CustomTask | None:
        stmt = (
            select(CustomTask)
            .join(TeacherTheme, CustomTask.theme_id == TeacherTheme.id)
            .where(
                CustomTask.id == task_id,
                TeacherTheme.teacher_id == teacher_id,
            )
            .options(joinedload(CustomTask.theme))
        )
        return await self._session.scalar(stmt)

    async def add_task(self, task: CustomTask) -> CustomTask:
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def delete_task(self, task: CustomTask) -> None:
        await self._session.delete(task)
