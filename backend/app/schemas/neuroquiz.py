"""Pydantic schemas for neuroquiz API."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class NeuroQuizOption(BaseModel):
    id: str
    text: str


class NeuroQuizQuestionPublic(BaseModel):
    id: uuid.UUID
    prompt: str
    options: list[NeuroQuizOption]


class NeuroQuizSession(BaseModel):
    topic: str
    chunk_idx: int
    scoring_enabled: bool
    questions: list[NeuroQuizQuestionPublic]


class NeuroQuizAnswerRequest(BaseModel):
    question_id: uuid.UUID
    option_id: str = Field(min_length=1, max_length=64)


class NeuroQuizSubmitResult(BaseModel):
    correct: bool
    correct_option_id: str
    explanation: str | None = None
    points_awarded: int
    quiz_completed: bool


class NeuroQuizVoteRequest(BaseModel):
    value: Literal["like", "dislike"]


class NeuroQuizWarmupStatus(BaseModel):
    status: Literal["ready", "pending", "failed"]

    model_config = ConfigDict(extra="forbid")
