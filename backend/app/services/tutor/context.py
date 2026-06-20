"""Tutor agent runtime context (per user / track / test gating)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextvars import ContextVar
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal, TypeVar

from app.services.rag.documents import ExamTrack

if TYPE_CHECKING:
    from app.services.tutor.student_tools import StudentTutorToolsService
    from app.services.tutor.teacher_tools import TeacherTutorToolsService

TutorRole = Literal["student", "teacher"]
T = TypeVar("T")
AsyncRunner = Callable[[Awaitable[T]], T]


@dataclass(frozen=True, slots=True)
class TutorRunContext:
    track: ExamTrack
    user_id: str = "anonymous"
    role: TutorRole = "student"
    active_test_session_id: uuid.UUID | None = None
    allowed_solve_test_id: int | None = None
    solve_student_answer: str | None = None
    run_async: AsyncRunner | None = field(default=None, compare=False, repr=False)
    student_tools_service: StudentTutorToolsService | None = field(
        default=None,
        compare=False,
        repr=False,
    )
    teacher_tools_service: TeacherTutorToolsService | None = field(
        default=None,
        compare=False,
        repr=False,
    )


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
