"""Homework template endpoints.

Registered with prefix ``/api/homework/templates`` and included in the app
*before* ``/{assignment_id}`` routes so ``templates`` is not parsed as a UUID.

| Method | Path                            | Role    | Description        |
|--------|---------------------------------|---------|--------------------|
| GET    | /api/homework/templates         | teacher | List own templates |
| POST   | /api/homework/templates         | teacher | Create template    |
| GET    | /api/homework/templates/{id}    | teacher | Get template       |
| PATCH  | /api/homework/templates/{id}    | teacher | Update template    |
| DELETE | /api/homework/templates/{id}    | teacher | Delete template    |
| POST   | /api/homework/templates/{id}/assign | teacher | Assign to student |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import TeacherUser, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.homework import HomeworkRead
from app.schemas.homework_templates import (
    HomeworkTemplateAssignRequest,
    HomeworkTemplateCreate,
    HomeworkTemplateRead,
    HomeworkTemplateUpdate,
)
from app.services.homework_template_service import HomeworkTemplateService

router = APIRouter(prefix="/api/homework/templates", tags=["homework-templates"])


@router.get("", response_model=list[HomeworkTemplateRead])
async def list_templates(
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[HomeworkTemplateRead]:
    return await HomeworkTemplateService(db).list_templates(teacher)


@router.post("", response_model=HomeworkTemplateRead, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: HomeworkTemplateCreate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkTemplateRead:
    return await HomeworkTemplateService(db).create_template(teacher, payload)


@router.post(
    "/{template_id}/assign",
    response_model=list[HomeworkRead],
    status_code=status.HTTP_201_CREATED,
)
async def assign_template(
    template_id: uuid.UUID,
    payload: HomeworkTemplateAssignRequest,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> list[HomeworkRead]:
    return await HomeworkTemplateService(db, settings).assign(
        teacher, template_id, payload
    )


@router.get("/{template_id}", response_model=HomeworkTemplateRead)
async def get_template(
    template_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkTemplateRead:
    return await HomeworkTemplateService(db).get_template(teacher, template_id)


@router.patch("/{template_id}", response_model=HomeworkTemplateRead)
async def update_template(
    template_id: uuid.UUID,
    payload: HomeworkTemplateUpdate,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeworkTemplateRead:
    return await HomeworkTemplateService(db).update_template(
        teacher, template_id, payload
    )


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid.UUID,
    teacher: TeacherUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    await HomeworkTemplateService(db).delete_template(teacher, template_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
