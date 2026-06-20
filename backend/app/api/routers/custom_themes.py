"""Student endpoints for published custom themes (SPEC §1.9.3).

| Method | Path               | Role    | Description                          |
|--------|--------------------|---------|--------------------------------------|
| GET    | /api/custom-themes | student | Published themes from own teacher    |
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import StudentUser, get_activity_service, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.custom_theme import CustomThemeListItem
from app.services.activity_service import ActivityService
from app.services.custom_test_session_service import CustomTestSessionService

router = APIRouter(prefix="/api/custom-themes", tags=["custom-themes"])


def get_custom_test_session_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    activity: Annotated[ActivityService, Depends(get_activity_service)],
) -> CustomTestSessionService:
    return CustomTestSessionService(db, settings, activity)


@router.get("", response_model=list[CustomThemeListItem])
async def list_custom_themes(
    student: StudentUser,
    service: Annotated[
        CustomTestSessionService, Depends(get_custom_test_session_service)
    ],
) -> list[CustomThemeListItem]:
    return await service.list_published_themes(student)
