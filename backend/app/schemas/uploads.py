"""Pydantic schemas for image upload API."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class UploadImageResponse(BaseModel):
    id: uuid.UUID
    url: str

    model_config = ConfigDict(from_attributes=True)


class UploadAudioResponse(BaseModel):
    id: uuid.UUID
    url: str
    duration_sec: float | None = None

    model_config = ConfigDict(from_attributes=True)
