"""Homework template business logic."""

from __future__ import annotations

import copy
import uuid

from fastapi import HTTPException, status
from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.models import (
    HomeworkAssignment,
    HomeworkItemProgress,
    HomeworkStatus,
    HomeworkTemplate,
    User,
)
from app.models.enums import HomeworkItemKind
from app.repositories.app.homework_repo import HomeworkRepository
from app.repositories.app.homework_template_repo import HomeworkTemplateRepository
from app.repositories.app.student_group_repo import StudentGroupRepository
from app.repositories.app.student_repo import StudentRepository
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.schemas.homework import CustomThemeHomeworkItem, HomeworkItem, HomeworkRead
from app.schemas.homework_templates import (
    HomeworkTemplateAssignRequest,
    HomeworkTemplateCreate,
    HomeworkTemplateRead,
    HomeworkTemplateUpdate,
)
from app.services.homework_mapper import to_homework_read
from app.services.homework_validation import validate_homework_items
from app.services.track_compat import assert_items_compatible_with_track

_ITEMS_ADAPTER = TypeAdapter(list[HomeworkItem])


class HomeworkTemplateService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self._session = session
        self._settings = settings or get_settings()
        self._repo = HomeworkTemplateRepository(session)
        self._homework = HomeworkRepository(session)
        self._students = StudentRepository(session)
        self._groups = StudentGroupRepository(session)
        self._themes = TeacherThemeRepository(session)

    async def list_templates(self, teacher: User) -> list[HomeworkTemplateRead]:
        templates = await self._repo.list_by_teacher(teacher.id)
        return [HomeworkTemplateRead.model_validate(t) for t in templates]

    async def create_template(
        self,
        teacher: User,
        data: HomeworkTemplateCreate,
    ) -> HomeworkTemplateRead:
        await self._validate_custom_themes(teacher.id, data.items)
        template = HomeworkTemplate(
            teacher_id=teacher.id,
            title=data.title,
            description=data.description,
            items=[
                item.model_dump(mode="json", exclude_none=True) for item in data.items
            ],
        )
        created = await self._repo.add(template)
        await self._session.commit()
        return HomeworkTemplateRead.model_validate(created)

    async def get_template(
        self,
        teacher: User,
        template_id: uuid.UUID,
    ) -> HomeworkTemplateRead:
        template = await self._require_template(teacher.id, template_id)
        return HomeworkTemplateRead.model_validate(template)

    async def update_template(
        self,
        teacher: User,
        template_id: uuid.UUID,
        data: HomeworkTemplateUpdate,
    ) -> HomeworkTemplateRead:
        template = await self._require_template(teacher.id, template_id)
        updates = data.model_dump(exclude_unset=True)
        if "items" in updates and data.items is not None:
            await self._validate_custom_themes(teacher.id, data.items)
            updates["items"] = [
                item.model_dump(mode="json", exclude_none=True) for item in data.items
            ]
        for field, value in updates.items():
            setattr(template, field, value)
        await self._session.flush()
        await self._session.refresh(template)
        await self._session.commit()
        return HomeworkTemplateRead.model_validate(template)

    async def delete_template(
        self,
        teacher: User,
        template_id: uuid.UUID,
    ) -> None:
        template = await self._require_template(teacher.id, template_id)
        await self._repo.delete(template)
        await self._session.commit()

    async def assign(
        self,
        teacher: User,
        template_id: uuid.UUID,
        data: HomeworkTemplateAssignRequest,
    ) -> list[HomeworkRead]:
        template = await self._require_template(teacher.id, template_id)
        typed_items = _ITEMS_ADAPTER.validate_python(template.items)

        if data.student_id is not None:
            assignment = await self._create_assignment_for_student(
                teacher=teacher,
                template=template,
                typed_items=typed_items,
                student_id=data.student_id,
                due_at=data.due_at,
                source_group_id=None,
                assign_batch_id=None,
            )
            await self._session.commit()
            reloaded = await self._homework.get_by_id(assignment.id)
            assert reloaded is not None
            return [to_homework_read(reloaded, include_student_email=True)]

        assert data.group_id is not None
        return await self._assign_to_group(
            teacher=teacher,
            template=template,
            typed_items=typed_items,
            group_id=data.group_id,
            due_at=data.due_at,
        )

    async def _assign_to_group(
        self,
        *,
        teacher: User,
        template: HomeworkTemplate,
        typed_items: list[HomeworkItem],
        group_id: uuid.UUID,
        due_at,
    ) -> list[HomeworkRead]:
        group = await self._groups.get_for_teacher(
            group_id,
            teacher.id,
            with_members=True,
        )
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        if not group.members:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot assign to an empty group",
            )

        # Validate all members first — all-or-nothing (no partial creates).
        member_students: list[User] = []
        for member in group.members:
            student = await self._students.get_student_for_teacher(
                member.student_user_id,
                teacher.id,
                active_only=True,
            )
            if student is None or student.student_profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found",
                )
            await self._validate_for_student(teacher, typed_items, student)
            member_students.append(student)

        created_ids: list[uuid.UUID] = []
        assign_batch_id = uuid.uuid4()
        for student in member_students:
            assignment = await self._create_assignment_for_student(
                teacher=teacher,
                template=template,
                typed_items=typed_items,
                student_id=student.id,
                due_at=due_at,
                source_group_id=group.id,
                assign_batch_id=assign_batch_id,
                student=student,
            )
            created_ids.append(assignment.id)

        await self._session.commit()

        results: list[HomeworkRead] = []
        for assignment_id in created_ids:
            reloaded = await self._homework.get_by_id(assignment_id)
            assert reloaded is not None
            results.append(to_homework_read(reloaded, include_student_email=True))
        return results

    async def _create_assignment_for_student(
        self,
        *,
        teacher: User,
        template: HomeworkTemplate,
        typed_items: list[HomeworkItem],
        student_id: uuid.UUID,
        due_at,
        source_group_id: uuid.UUID | None,
        assign_batch_id: uuid.UUID | None = None,
        student: User | None = None,
    ) -> HomeworkAssignment:
        if student is None:
            student = await self._students.get_student_for_teacher(
                student_id,
                teacher.id,
                active_only=True,
            )
            if student is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student not found",
                )
            if student.student_profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Student profile not found",
                )
            await self._validate_for_student(teacher, typed_items, student)

        items_snapshot = copy.deepcopy(template.items)
        assignment = HomeworkAssignment(
            student_id=student.id,
            teacher_id=teacher.id,
            title=template.title,
            description=template.description,
            due_at=due_at,
            items=items_snapshot,
            status=HomeworkStatus.ASSIGNED,
            template_id=template.id,
            source_group_id=source_group_id,
            assign_batch_id=assign_batch_id,
            item_progress=[
                HomeworkItemProgress(
                    item_index=index,
                    kind=HomeworkItemKind(item["kind"]),
                    completed=False,
                )
                for index, item in enumerate(items_snapshot)
            ],
        )
        await self._homework.add(assignment)
        return assignment

    async def _validate_for_student(
        self,
        teacher: User,
        typed_items: list[HomeworkItem],
        student: User,
    ) -> None:
        profile = student.student_profile
        assert profile is not None
        assert_items_compatible_with_track(
            typed_items,
            student_track=profile.track,
            settings=self._settings,
        )
        await validate_homework_items(
            typed_items,
            track=profile.track,
            teacher_id=teacher.id,
            settings=self._settings,
            session=self._session,
        )

    async def _require_template(
        self,
        teacher_id: uuid.UUID,
        template_id: uuid.UUID,
    ) -> HomeworkTemplate:
        template = await self._repo.get_for_teacher(template_id, teacher_id)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found",
            )
        return template

    async def _validate_custom_themes(
        self,
        teacher_id: uuid.UUID,
        items: list[HomeworkItem],
    ) -> None:
        for item in items:
            if not isinstance(item, CustomThemeHomeworkItem):
                continue
            theme = await self._themes.get_for_teacher(item.theme_id, teacher_id)
            if theme is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Custom theme not found",
                )
