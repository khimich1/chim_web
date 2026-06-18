"""Task bank helpers for tutor tools."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import get_settings
from app.repositories.content.tests import ExamContentRepo
from app.services.rag.documents import ExamTrack

_PREVIEW_LEN = 200

_IMAGE_MARKERS: tuple[str, ...] = (
    "рисунок",
    "рис.",
    "изображени",
    "на рисунке",
    "по рисунку",
    "схеме",
    "схема",
    "таблиц",
    "график",
)


def question_requires_image(question: str) -> bool:
    lowered = question.lower()
    return any(marker in lowered for marker in _IMAGE_MARKERS)


@dataclass(frozen=True, slots=True)
class TaskCard:
    id: int
    type: int
    question_preview: str


@dataclass(frozen=True, slots=True)
class PracticeTaskCard:
    id: int
    type: int
    question: str


def _repo_for_track(track: ExamTrack) -> ExamContentRepo:
    settings = get_settings()
    return ExamContentRepo(settings.tests_db_path_for_track(track))


def get_task(task_id: int, *, track: ExamTrack):
    return _repo_for_track(track).get_question(task_id)


def search_tasks(
    *,
    track: ExamTrack,
    query: str | None = None,
    task_type: int | None = None,
    top_k: int = 5,
) -> list[TaskCard]:
    questions = _repo_for_track(track).search_questions(
        query=query,
        task_type=task_type,
        limit=top_k,
    )
    return [
        TaskCard(
            id=item.id,
            type=item.type,
            question_preview=(item.question or "")[:_PREVIEW_LEN],
        )
        for item in questions
    ]


def search_practice_tasks(
    *,
    track: ExamTrack,
    query: str | None = None,
    task_type: int | None = None,
    top_k: int = 5,
) -> list[PracticeTaskCard]:
    """Search tasks for practice — full question text, no correct_ans in payload."""
    questions = _repo_for_track(track).search_questions(
        query=query,
        task_type=task_type,
        limit=top_k,
    )
    return [
        PracticeTaskCard(
            id=item.id,
            type=item.type,
            question=item.question or "",
        )
        for item in questions
    ]
