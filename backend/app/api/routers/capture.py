"""Mobile capture endpoints for QR handoff (SPEC §1.9.9).

| Method | Path                 | Auth              | Response              |
|--------|----------------------|-------------------|-----------------------|
| GET    | /api/capture/{token} | token in URL      | CaptureMetaResponse   |
| POST   | /api/capture/{token} | token in URL      | CaptureUploadResponse |
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_app_settings
from app.core.config import Settings
from app.db.session import get_db
from app.schemas.handoff import CaptureMetaResponse, CaptureUploadResponse
from app.services.upload_handoff_service import UploadHandoffService

router = APIRouter(prefix="/api/capture", tags=["capture"])


def get_upload_handoff_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> UploadHandoffService:
    return UploadHandoffService(db, settings)


@router.get("/{token}", response_model=CaptureMetaResponse)
async def get_capture_meta(
    token: uuid.UUID,
    service: Annotated[UploadHandoffService, Depends(get_upload_handoff_service)],
) -> CaptureMetaResponse:
    return await service.get_capture_meta(token)


@router.post("/{token}", response_model=CaptureUploadResponse)
async def capture_upload(
    token: uuid.UUID,
    service: Annotated[UploadHandoffService, Depends(get_upload_handoff_service)],
    file: UploadFile = File(...),
) -> CaptureUploadResponse:
    return await service.capture_upload(token, file)
