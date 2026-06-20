"""Image upload business logic (SPEC §1.9.7)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings
from app.models import UploadedImage, User
from app.repositories.app.upload_repo import UploadedImageRepository
from app.schemas.uploads import UploadImageResponse

_MIME_EXTENSIONS: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


class UploadService:
    def __init__(
        self,
        repo: UploadedImageRepository,
        settings: Settings,
    ) -> None:
        self._repo = repo
        self._settings = settings

    async def save_image(
        self,
        owner: User,
        upload: UploadFile,
    ) -> UploadImageResponse:
        content_type = upload.content_type or ""
        if content_type not in self._settings.upload_allowed_mime:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported image MIME type",
            )

        data = await upload.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Empty upload",
            )
        if len(data) > self._settings.upload_max_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Image exceeds maximum allowed size",
            )

        extension = _MIME_EXTENSIONS[content_type]
        stored_filename = f"{uuid.uuid4()}{extension}"
        upload_dir = self._settings.upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / stored_filename
        file_path.write_bytes(data)

        image = await self._repo.create(
            owner_id=owner.id,
            stored_filename=stored_filename,
            mime_type=content_type,
            size_bytes=len(data),
        )
        return UploadImageResponse(
            id=image.id,
            url=f"/api/uploads/images/{image.id}",
        )

    async def get_image_for_user(
        self,
        image_id: uuid.UUID,
        user: User,
    ) -> tuple[UploadedImage, Path]:
        image = await self._repo.get_by_id(image_id)
        if image is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            )
        if image.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to access this image",
            )

        file_path = self._resolve_file_path(image.stored_filename)
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file missing",
            )
        return image, file_path

    def _resolve_file_path(self, stored_filename: str) -> Path:
        upload_dir = self._settings.upload_dir.resolve()
        file_path = (upload_dir / stored_filename).resolve()
        if upload_dir not in file_path.parents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file missing",
            )
        return file_path
