"""Teacher theme and custom task endpoints (SPEC §1.9).

| Method | Path                              | Role    | Description              |
|--------|-----------------------------------|---------|--------------------------|
| GET    | /api/teacher/themes               | teacher | List own themes          |
| POST   | /api/teacher/themes               | teacher | Create theme             |
| GET    | /api/teacher/themes/{id}          | teacher | Get theme                |
| PATCH  | /api/teacher/themes/{id}          | teacher | Update theme             |
| DELETE | /api/teacher/themes/{id}          | teacher | Delete theme             |
| GET    | /api/teacher/themes/{id}/tasks    | teacher | List tasks in theme      |
| POST   | /api/teacher/themes/{id}/tasks    | teacher | Create task in theme     |
| GET    | /api/teacher/tasks/{id}           | teacher | Get task                 |
| PATCH  | /api/teacher/tasks/{id}           | teacher | Update task              |
| DELETE | /api/teacher/tasks/{id}           | teacher | Delete task              |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TeacherUser
from app.db.session import get_db
from app.schemas.custom_task import (
    CustomTaskCreate,
    CustomTaskRead,
    CustomTaskUpdate,
    ThemeCreate,
    ThemeRead,
    ThemeUpdate,
)
from app.services.teacher_theme_service import TeacherThemeService

router = APIRouter(prefix="/api/teacher", tags=["teacher-themes"])


@router.get("/themes", response_model=list[ThemeRead])
async def list_themes(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ThemeRead]:
    return await TeacherThemeService(db).list_themes(teacher.id)


@router.post("/themes", response_model=ThemeRead, status_code=status.HTTP_201_CREATED)
async def create_theme(
    payload: ThemeCreate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThemeRead:
    return await TeacherThemeService(db).create_theme(teacher.id, payload)


@router.get("/themes/{theme_id}", response_model=ThemeRead)
async def get_theme(
    theme_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThemeRead:
    return await TeacherThemeService(db).get_theme(theme_id, teacher.id)


@router.patch("/themes/{theme_id}", response_model=ThemeRead)
async def update_theme(
    theme_id: uuid.UUID,
    payload: ThemeUpdate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ThemeRead:
    return await TeacherThemeService(db).update_theme(theme_id, teacher.id, payload)


@router.delete("/themes/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_theme(
    theme_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await TeacherThemeService(db).delete_theme(theme_id, teacher.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/themes/{theme_id}/tasks", response_model=list[CustomTaskRead])
async def list_tasks(
    theme_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CustomTaskRead]:
    return await TeacherThemeService(db).list_tasks(theme_id, teacher.id)


@router.post(
    "/themes/{theme_id}/tasks",
    response_model=CustomTaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    theme_id: uuid.UUID,
    payload: CustomTaskCreate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CustomTaskRead:
    return await TeacherThemeService(db).create_task(theme_id, teacher.id, payload)


@router.get("/tasks/{task_id}", response_model=CustomTaskRead)
async def get_task(
    task_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CustomTaskRead:
    return await TeacherThemeService(db).get_task(task_id, teacher.id)


@router.patch("/tasks/{task_id}", response_model=CustomTaskRead)
async def update_task(
    task_id: uuid.UUID,
    payload: CustomTaskUpdate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CustomTaskRead:
    return await TeacherThemeService(db).update_task(task_id, teacher.id, payload)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await TeacherThemeService(db).delete_task(task_id, teacher.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
