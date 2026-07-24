"""Data access for teacher student groups."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    HomeworkAssignment,
    HomeworkStatus,
    StudentGroup,
    StudentGroupMember,
    User,
)

_DEFAULT_NAME_RE = re.compile(r"^Группа (\d+)$")


class StudentGroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_teacher(
        self,
        teacher_id: uuid.UUID,
    ) -> list[tuple[StudentGroup, int]]:
        stmt = (
            select(
                StudentGroup,
                func.count(StudentGroupMember.id).label("member_count"),
            )
            .outerjoin(
                StudentGroupMember,
                StudentGroupMember.group_id == StudentGroup.id,
            )
            .where(StudentGroup.teacher_id == teacher_id)
            .group_by(StudentGroup.id)
            .order_by(StudentGroup.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return [(row[0], int(row[1])) for row in result.all()]

    async def get_for_teacher(
        self,
        group_id: uuid.UUID,
        teacher_id: uuid.UUID,
        *,
        with_members: bool = False,
    ) -> StudentGroup | None:
        stmt = select(StudentGroup).where(
            StudentGroup.id == group_id,
            StudentGroup.teacher_id == teacher_id,
        )
        if with_members:
            stmt = stmt.options(
                selectinload(StudentGroup.members)
                .selectinload(StudentGroupMember.student)
                .selectinload(User.student_profile)
            )
        return await self._session.scalar(stmt)

    async def list_names_for_teacher(self, teacher_id: uuid.UUID) -> list[str]:
        stmt = select(StudentGroup.name).where(StudentGroup.teacher_id == teacher_id)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def next_default_name(self, teacher_id: uuid.UUID) -> str:
        names = await self.list_names_for_teacher(teacher_id)
        taken = {
            int(match.group(1))
            for name in names
            if (match := _DEFAULT_NAME_RE.match(name))
        }
        n = 1
        while n in taken:
            n += 1
        return f"Группа {n}"

    async def add(self, group: StudentGroup) -> StudentGroup:
        self._session.add(group)
        await self._session.flush()
        await self._session.refresh(group)
        return group

    async def delete(self, group: StudentGroup) -> None:
        await self._session.delete(group)

    async def find_membership(
        self,
        student_user_id: uuid.UUID,
    ) -> StudentGroupMember | None:
        stmt = select(StudentGroupMember).where(
            StudentGroupMember.student_user_id == student_user_id
        )
        return await self._session.scalar(stmt)

    async def replace_members(
        self,
        group: StudentGroup,
        student_ids: list[uuid.UUID],
    ) -> None:
        existing = {member.student_user_id: member for member in list(group.members)}
        desired = set(student_ids)

        for student_id, member in list(existing.items()):
            if student_id not in desired:
                group.members.remove(member)

        for student_id in student_ids:
            if student_id not in existing:
                group.members.append(
                    StudentGroupMember(student_user_id=student_id)
                )
        await self._session.flush()

    async def revoke_unsubmitted_for_students(
        self,
        *,
        group_id: uuid.UUID,
        student_ids: list[uuid.UUID],
    ) -> int:
        if not student_ids:
            return 0
        stmt = (
            update(HomeworkAssignment)
            .where(
                HomeworkAssignment.source_group_id == group_id,
                HomeworkAssignment.student_id.in_(student_ids),
                HomeworkAssignment.status.in_(
                    [HomeworkStatus.ASSIGNED, HomeworkStatus.IN_PROGRESS]
                ),
            )
            .values(status=HomeworkStatus.CANCELLED)
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)

    async def revoke_all_unsubmitted(self, group_id: uuid.UUID) -> int:
        stmt = (
            update(HomeworkAssignment)
            .where(
                HomeworkAssignment.source_group_id == group_id,
                HomeworkAssignment.status.in_(
                    [HomeworkStatus.ASSIGNED, HomeworkStatus.IN_PROGRESS]
                ),
            )
            .values(status=HomeworkStatus.CANCELLED)
        )
        result = await self._session.execute(stmt)
        return int(result.rowcount or 0)
