"""Homework item validation against content DB (track-aware)."""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import Settings
from app.models.enums import ExamTrack, HomeworkItemKind
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo
from app.schemas.homework import HomeworkItem

MAX_TEST_BY_TYPE_QUESTIONS = 60
_TYPE_RANGES: dict[ExamTrack, range] = {
    ExamTrack.EGE: range(1, 29),
    ExamTrack.OGE: range(1, 20),
}


def validate_homework_items(
    items: list[HomeworkItem],
    *,
    track: ExamTrack,
    settings: Settings,
) -> None:
    """Reject invalid ``test_by_type`` specs before persisting an assignment."""
    repo = _content_repo(track, settings)
    for item in items:
        if item.kind != HomeworkItemKind.TEST_BY_TYPE:
            continue
        allowed = _TYPE_RANGES[track]
        invalid = [type_num for type_num in item.types if type_num not in allowed]
        if invalid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Task type(s) {invalid} are out of range for track "
                    f"{track.value} (allowed {allowed.start}–{allowed.stop - 1})"
                ),
            )
        try:
            question_count = repo.count_expanded_questions(item.types, track=track)
        except ContentDbError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Test content database unavailable",
            ) from exc
        if question_count == 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No questions found for the requested task type(s)",
            )
        if question_count > MAX_TEST_BY_TYPE_QUESTIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"test_by_type item expands to {question_count} questions; "
                    f"maximum is {MAX_TEST_BY_TYPE_QUESTIONS}"
                ),
            )


def _content_repo(track: ExamTrack, settings: Settings) -> ExamContentRepo:
    path = (
        settings.content_ege_db_path
        if track == ExamTrack.EGE
        else settings.content_oge_db_path
    )
    return ExamContentRepo(path)
