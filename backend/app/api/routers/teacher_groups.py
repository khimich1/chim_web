"""Teacher student group endpoints.

| Method | Path                                 | Role    | Description              |
|--------|--------------------------------------|---------|--------------------------|
| GET    | /api/teacher/groups                  | teacher | List groups + counts     |
| POST   | /api/teacher/groups                  | teacher | Create (default name)    |
| GET    | /api/teacher/groups/{id}             | teacher | Detail + members         |
| PATCH  | /api/teacher/groups/{id}             | teacher | Rename                   |
| DELETE | /api/teacher/groups/{id}             | teacher | Revoke + delete          |
| PUT    | /api/teacher/groups/{id}/members     | teacher | Replace members + revoke |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TeacherUser
from app.db.session import get_db
from app.schemas.groups import (
    StudentGroupCreate,
    StudentGroupDetailRead,
    StudentGroupMembersReplace,
    StudentGroupSummaryRead,
    StudentGroupUpdate,
)
from app.services.group_service import StudentGroupService

router = APIRouter(prefix="/api/teacher/groups", tags=["teacher-groups"])


@router.get("", response_model=list[StudentGroupSummaryRead])
async def list_groups(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StudentGroupSummaryRead]:
    return await StudentGroupService(db).list_groups(teacher)


@router.post(
    "",
    response_model=StudentGroupDetailRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: StudentGroupCreate | None = None,
) -> StudentGroupDetailRead:
    data = payload if payload is not None else StudentGroupCreate()
    return await StudentGroupService(db).create_group(teacher, data)


@router.get("/{group_id}", response_model=StudentGroupDetailRead)
async def get_group(
    group_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentGroupDetailRead:
    return await StudentGroupService(db).get_group(teacher, group_id)


@router.patch("/{group_id}", response_model=StudentGroupDetailRead)
async def rename_group(
    group_id: uuid.UUID,
    payload: StudentGroupUpdate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentGroupDetailRead:
    return await StudentGroupService(db).rename_group(teacher, group_id, payload)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await StudentGroupService(db).delete_group(teacher, group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{group_id}/members", response_model=StudentGroupDetailRead)
async def replace_group_members(
    group_id: uuid.UUID,
    payload: StudentGroupMembersReplace,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentGroupDetailRead:
    return await StudentGroupService(db).replace_members(teacher, group_id, payload)
