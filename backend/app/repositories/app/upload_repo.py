"""Data access for UploadedImage rows (app DB)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UploadedImage


class UploadedImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        owner_id: uuid.UUID,
        stored_filename: str,
        mime_type: str,
        size_bytes: int,
    ) -> UploadedImage:
        image = UploadedImage(
            owner_id=owner_id,
            stored_filename=stored_filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
        )
        self._session.add(image)
        await self._session.flush()
        return image

    async def get_by_id(self, image_id: uuid.UUID) -> UploadedImage | None:
        return await self._session.get(UploadedImage, image_id)
