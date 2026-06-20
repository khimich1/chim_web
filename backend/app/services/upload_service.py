"""Image and audio upload business logic (SPEC §1.9.7, §1.9.9)."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import Settings
from app.models import UploadedAudio, UploadedImage, User, UserRole
from app.repositories.app.upload_repo import UploadedAudioRepository, UploadedImageRepository
from app.schemas.uploads import UploadAudioResponse, UploadImageResponse
from app.utils.audio_duration import parse_audio_duration_sec as parse_audio_duration

_MIME_EXTENSIONS: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

_AUDIO_EXTENSIONS: dict[str, str] = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
}


class UploadService:
    def __init__(
        self,
        repo: UploadedImageRepository,
        settings: Settings,
        audio_repo: UploadedAudioRepository | None = None,
    ) -> None:
        self._repo = repo
        self._audio_repo = audio_repo
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
        if image.owner_id == user.id:
            pass
        elif user.role == UserRole.TEACHER and (
            await self._repo.teacher_can_view_answer_image(user.id, image_id)
            or await self._repo.teacher_can_view_feedback_image(user.id, image_id)
        ):
            pass
        elif user.role == UserRole.STUDENT and await self._repo.student_can_view_image(
            user.id, image_id
        ):
            pass
        else:
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

    async def save_audio(
        self,
        owner: User,
        upload: UploadFile,
        *,
        duration_sec: float | None = None,
    ) -> UploadAudioResponse:
        if owner.role != UserRole.TEACHER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can upload audio feedback",
            )
        if self._audio_repo is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio upload not configured",
            )

        content_type = upload.content_type or ""
        if content_type not in self._settings.upload_audio_allowed_mime:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unsupported audio MIME type",
            )

        data = await upload.read()
        if not data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Empty upload",
            )
        if len(data) > self._settings.upload_audio_max_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio exceeds maximum allowed size",
            )

        parsed_duration = parse_audio_duration(data, content_type)
        effective_duration = parsed_duration if parsed_duration is not None else duration_sec
        if effective_duration is not None and effective_duration > self._settings.upload_audio_max_duration_sec:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Audio duration exceeds maximum allowed length",
            )

        extension = _AUDIO_EXTENSIONS[content_type]
        stored_filename = f"{uuid.uuid4()}{extension}"
        upload_dir = self._settings.upload_dir
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / stored_filename
        file_path.write_bytes(data)

        audio = await self._audio_repo.create(
            owner_id=owner.id,
            stored_filename=stored_filename,
            mime_type=content_type,
            size_bytes=len(data),
            duration_sec=effective_duration,
        )
        return UploadAudioResponse(
            id=audio.id,
            url=f"/api/uploads/audio/{audio.id}",
            duration_sec=effective_duration,
        )

    async def get_audio_for_user(
        self,
        audio_id: uuid.UUID,
        user: User,
    ) -> tuple[UploadedAudio, Path]:
        if self._audio_repo is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio download not configured",
            )

        audio = await self._audio_repo.get_by_id(audio_id)
        if audio is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio not found",
            )
        if audio.owner_id == user.id:
            pass
        elif user.role == UserRole.TEACHER and await self._audio_repo.teacher_can_view_audio(
            user.id, audio_id
        ):
            pass
        elif user.role == UserRole.STUDENT and await self._audio_repo.student_can_view_audio(
            user.id, audio_id
        ):
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to access this audio",
            )

        file_path = self._resolve_file_path(audio.stored_filename)
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audio file missing",
            )
        return audio, file_path

    def _resolve_file_path(self, stored_filename: str) -> Path:
        upload_dir = self._settings.upload_dir.resolve()
        file_path = (upload_dir / stored_filename).resolve()
        if upload_dir not in file_path.parents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image file missing",
            )
        return file_path
