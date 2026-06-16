"""Test catalog API schemas (no answers, hints, or explanations in list views)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VariantRead(BaseModel):
    filename: str


class QuestionRead(BaseModel):
    """Public question metadata for students (before answering)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    type: int
    question: str
    options: str | None = None
