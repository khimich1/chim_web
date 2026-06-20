"""Image upload endpoints (SPEC §1.9.7).

| Method | Path                        | Role              | Response            |
|--------|-----------------------------|-------------------|---------------------|
| POST   | /api/uploads/images         | teacher, student  | UploadImageResponse |
| GET    | /api/uploads/images/{id}      | auth (owner)      | image stream        |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.repositories.app.upload_repo import UploadedImageRepository
from app.schemas.uploads import UploadImageResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/api/uploads", tags=["uploads"])


def get_upload_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> UploadService:
    return UploadService(UploadedImageRepository(db), settings)


@router.post("/images", response_model=UploadImageResponse, status_code=201)
async def upload_image(
    user: CurrentUser,
    service: Annotated[UploadService, Depends(get_upload_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> UploadImageResponse:
    result = await service.save_image(user, file)
    await db.commit()
    return result


@router.get("/images/{image_id}")
async def get_image(
    image_id: uuid.UUID,
    user: CurrentUser,
    service: Annotated[UploadService, Depends(get_upload_service)],
) -> FileResponse:
    image, file_path = await service.get_image_for_user(image_id, user)
    return FileResponse(
        path=file_path,
        media_type=image.mime_type,
        filename=image.stored_filename,
    )
