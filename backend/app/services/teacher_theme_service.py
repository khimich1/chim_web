"""Teacher theme and custom task business logic (SPEC §1.9)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CustomTask, TeacherTheme
from app.models.enums import GradingMode
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.schemas.custom_task import (
    CustomTaskCreate,
    CustomTaskRead,
    CustomTaskUpdate,
    ThemeCreate,
    ThemeRead,
    ThemeUpdate,
)


class TeacherThemeService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TeacherThemeRepository(session)

    async def list_themes(self, teacher_id: uuid.UUID) -> list[ThemeRead]:
        rows = await self._repo.list_by_teacher_with_task_counts(teacher_id)
        return [
            ThemeRead.model_validate(theme).model_copy(update={"task_count": count})
            for theme, count in rows
        ]

    async def create_theme(
        self,
        teacher_id: uuid.UUID,
        data: ThemeCreate,
    ) -> ThemeRead:
        theme = TeacherTheme(
            teacher_id=teacher_id,
            title=data.title,
            description=data.description,
            is_published=data.is_published,
            sort_order=data.sort_order,
        )
        created = await self._repo.add_theme(theme)
        await self._session.commit()
        return ThemeRead.model_validate(created)

    async def get_theme(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> ThemeRead:
        theme = await self._require_theme(theme_id, teacher_id)
        return ThemeRead.model_validate(theme)

    async def update_theme(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
        data: ThemeUpdate,
    ) -> ThemeRead:
        theme = await self._require_theme(theme_id, teacher_id)
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(theme, field, value)
        await self._session.flush()
        await self._session.refresh(theme)
        await self._session.commit()
        return ThemeRead.model_validate(theme)

    async def delete_theme(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> None:
        theme = await self._require_theme(theme_id, teacher_id)
        await self._repo.delete_theme(theme)
        await self._session.commit()

    async def list_tasks(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> list[CustomTaskRead]:
        await self._require_theme(theme_id, teacher_id)
        tasks = await self._repo.list_tasks(theme_id)
        return [CustomTaskRead.model_validate(task) for task in tasks]

    async def create_task(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
        data: CustomTaskCreate,
    ) -> CustomTaskRead:
        await self._require_theme(theme_id, teacher_id)
        task = CustomTask(
            theme_id=theme_id,
            title=data.title,
            sort_order=data.sort_order,
            grading_mode=data.grading_mode,
            question_blocks=_blocks_to_json(data.question_blocks),
            reference_answer=_blocks_to_json(data.reference_answer),
            correct_value=data.correct_value,
        )
        created = await self._repo.add_task(task)
        await self._session.commit()
        return CustomTaskRead.model_validate(created)

    async def get_task(
        self,
        task_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> CustomTaskRead:
        task = await self._require_task(task_id, teacher_id)
        return CustomTaskRead.model_validate(task)

    async def update_task(
        self,
        task_id: uuid.UUID,
        teacher_id: uuid.UUID,
        data: CustomTaskUpdate,
    ) -> CustomTaskRead:
        task = await self._require_task(task_id, teacher_id)
        updates = data.model_dump(exclude_unset=True)
        if not updates:
            return CustomTaskRead.model_validate(task)

        if "question_blocks" in updates:
            updates["question_blocks"] = _blocks_to_json(updates["question_blocks"])
        if "reference_answer" in updates:
            updates["reference_answer"] = _blocks_to_json(
                updates["reference_answer"]
            )

        for field, value in updates.items():
            setattr(task, field, value)

        self._validate_task_fields(task)
        await self._session.flush()
        await self._session.refresh(task)
        await self._session.commit()
        return CustomTaskRead.model_validate(task)

    async def delete_task(
        self,
        task_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> None:
        task = await self._require_task(task_id, teacher_id)
        await self._repo.delete_task(task)
        await self._session.commit()

    async def _require_theme(
        self,
        theme_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> TeacherTheme:
        theme = await self._repo.get_for_teacher(theme_id, teacher_id)
        if theme is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Theme not found",
            )
        return theme

    async def _require_task(
        self,
        task_id: uuid.UUID,
        teacher_id: uuid.UUID,
    ) -> CustomTask:
        task = await self._repo.get_task_for_teacher(task_id, teacher_id)
        if task is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        return task

    @staticmethod
    def _validate_task_fields(task: CustomTask) -> None:
        if task.grading_mode == GradingMode.AUTO:
            if not task.correct_value or not task.correct_value.strip():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="auto grading_mode requires correct_value",
                )
        elif task.grading_mode == GradingMode.SELF_CHECK:
            if not task.reference_answer:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="self_check grading_mode requires reference_answer blocks",
                )


def _blocks_to_json(blocks: list | None) -> list[dict] | None:
    if blocks is None:
        return None
    return [block.model_dump() if hasattr(block, "model_dump") else block for block in blocks]
