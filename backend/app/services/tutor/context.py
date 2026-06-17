"""Tutor agent runtime context (per user / track / test gating)."""

from __future__ import annotations

from contextvars import ContextVar
import uuid
from dataclasses import dataclass
from typing import Literal

from app.services.rag.documents import ExamTrack

TutorRole = Literal["student", "teacher"]


@dataclass(frozen=True, slots=True)
class TutorRunContext:
    track: ExamTrack
    user_id: str = "anonymous"
    role: TutorRole = "student"
    active_test_session_id: uuid.UUID | None = None


_tutor_context: ContextVar[TutorRunContext | None] = ContextVar(
    "tutor_context",
    default=None,
)


def set_tutor_context(ctx: TutorRunContext) -> None:
    _tutor_context.set(ctx)


def get_tutor_context() -> TutorRunContext:
    ctx = _tutor_context.get()
    if ctx is None:
        return TutorRunContext(track="ege")
    return ctx


def clear_tutor_context() -> None:
    _tutor_context.set(None)
