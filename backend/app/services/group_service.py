"""Teacher student group business logic."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StudentGroup, User
from app.repositories.app.student_group_repo import StudentGroupRepository
from app.repositories.app.student_repo import StudentRepository
from app.schemas.groups import (
    StudentGroupCreate,
    StudentGroupDetailRead,
    StudentGroupMemberRead,
    StudentGroupMembersReplace,
    StudentGroupSummaryRead,
    StudentGroupUpdate,
)


class StudentGroupService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._groups = StudentGroupRepository(session)
        self._students = StudentRepository(session)

    async def list_groups(self, teacher: User) -> list[StudentGroupSummaryRead]:
        rows = await self._groups.list_by_teacher(teacher.id)
        return [
            StudentGroupSummaryRead(
                id=group.id,
                teacher_id=group.teacher_id,
                name=group.name,
                member_count=count,
                created_at=group.created_at,
            )
            for group, count in rows
        ]

    async def create_group(
        self,
        teacher: User,
        data: StudentGroupCreate,
    ) -> StudentGroupDetailRead:
        name = data.name
        if name is None:
            name = await self._groups.next_default_name(teacher.id)
        group = StudentGroup(teacher_id=teacher.id, name=name)
        created = await self._groups.add(group)
        await self._session.commit()
        return await self.get_group(teacher, created.id)

    async def get_group(
        self,
        teacher: User,
        group_id: uuid.UUID,
    ) -> StudentGroupDetailRead:
        group = await self._require_group(teacher.id, group_id, with_members=True)
        return _to_detail(group)

    async def rename_group(
        self,
        teacher: User,
        group_id: uuid.UUID,
        data: StudentGroupUpdate,
    ) -> StudentGroupDetailRead:
        group = await self._require_group(teacher.id, group_id, with_members=True)
        group.name = data.name
        await self._session.flush()
        await self._session.commit()
        return await self.get_group(teacher, group_id)

    async def delete_group(
        self,
        teacher: User,
        group_id: uuid.UUID,
    ) -> None:
        group = await self._require_group(teacher.id, group_id, with_members=True)
        await self._groups.revoke_all_unsubmitted(group.id)
        await self._groups.delete(group)
        await self._session.commit()

    async def replace_members(
        self,
        teacher: User,
        group_id: uuid.UUID,
        data: StudentGroupMembersReplace,
    ) -> StudentGroupDetailRead:
        group = await self._require_group(teacher.id, group_id, with_members=True)
        desired_ids = list(dict.fromkeys(data.student_ids))

        for student_id in desired_ids:
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
            existing = await self._groups.find_membership(student_id)
            if existing is not None and existing.group_id != group.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Student already belongs to another group",
                )

        current_ids = {member.student_user_id for member in group.members}
        desired_set = set(desired_ids)
        removed = list(current_ids - desired_set)
        if removed:
            await self._groups.revoke_unsubmitted_for_students(
                group_id=group.id,
                student_ids=removed,
            )

        await self._groups.replace_members(group, desired_ids)
        await self._session.commit()
        return await self.get_group(teacher, group_id)

    async def _require_group(
        self,
        teacher_id: uuid.UUID,
        group_id: uuid.UUID,
        *,
        with_members: bool,
    ) -> StudentGroup:
        group = await self._groups.get_for_teacher(
            group_id,
            teacher_id,
            with_members=with_members,
        )
        if group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Group not found",
            )
        return group


def _to_detail(group: StudentGroup) -> StudentGroupDetailRead:
    members: list[StudentGroupMemberRead] = []
    for member in group.members:
        student = member.student
        track = None
        if student is not None and student.student_profile is not None:
            track = student.student_profile.track.value
        members.append(
            StudentGroupMemberRead(
                id=member.student_user_id,
                email=student.email if student is not None else "",
                track=track,
            )
        )
    return StudentGroupDetailRead(
        id=group.id,
        teacher_id=group.teacher_id,
        name=group.name,
        member_count=len(members),
        created_at=group.created_at,
        members=members,
    )
