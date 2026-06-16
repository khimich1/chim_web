"""Students endpoints (teacher-only).

| Method | Path            | Role    | Request        | Response           |
|--------|-----------------|---------|----------------|--------------------|
| GET    | /api/students   | teacher | -              | list[StudentRead]  |
| POST   | /api/students   | teacher | StudentCreate  | StudentRead (201)  |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TeacherUser
from app.db.session import get_db
from app.schemas.students import StudentCreate, StudentRead
from app.services.student_service import StudentService

router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
async def list_students(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StudentRead]:
    return await StudentService(db).list_students(teacher.id)


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(
    payload: StudentCreate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StudentRead:
    return await StudentService(db).create_student(teacher.id, payload)
