"""Homework endpoints (teacher assign, student list/detail/submit).

| Method | Path                      | Role              | Description        |
|--------|---------------------------|-------------------|--------------------|
| POST   | /api/homework             | teacher           | Create assignment  |
| GET    | /api/homework             | teacher / student | Role-based list    |
| GET    | /api/homework/{id}        | teacher / student | Details (RBAC)     |
| POST   | /api/homework/{id}/submit | student           | Submit homework    |
| POST   | /api/homework/{id}/items/{index}/complete | student | Mark lecture read |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, StudentUser, TeacherUser
from app.db.session import get_db
from app.schemas.homework import HomeworkCreate, HomeworkRead, HomeworkSubmitRequest
from app.services.homework_service import HomeworkService
from app.services.homework_submit_service import HomeworkSubmitService

router = APIRouter(prefix="/api/homework", tags=["homework"])


@router.post("", response_model=HomeworkRead, status_code=status.HTTP_201_CREATED)
async def create_homework(
    payload: HomeworkCreate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkRead:
    return await HomeworkService(db).create_assignment(teacher, payload)


@router.get("", response_model=list[HomeworkRead])
async def list_homework(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[HomeworkRead]:
    return await HomeworkService(db).list_assignments(user)


@router.get("/{assignment_id}", response_model=HomeworkRead)
async def get_homework(
    assignment_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkRead:
    return await HomeworkService(db).get_assignment(user, assignment_id)


@router.post("/{assignment_id}/submit", response_model=HomeworkRead)
async def submit_homework(
    assignment_id: uuid.UUID,
    payload: HomeworkSubmitRequest,
    student: StudentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkRead:
    return await HomeworkSubmitService(db).submit(student, assignment_id, payload)


@router.post(
    "/{assignment_id}/items/{item_index}/complete",
    response_model=HomeworkRead,
)
async def complete_homework_item(
    assignment_id: uuid.UUID,
    item_index: int,
    student: StudentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkRead:
    return await HomeworkSubmitService(db).complete_item(
        student, assignment_id, item_index
    )
