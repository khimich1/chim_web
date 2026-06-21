"""Homework item validation against content DB (track-aware)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.enums import ExamTrack
from app.repositories.app.teacher_theme_repo import TeacherThemeRepository
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo
from app.schemas.homework import (
    CustomThemeHomeworkItem,
    HomeworkItem,
    TestByTypeItem,
    TestPartialItem,
    TestVariantItem,
)

MAX_TEST_BY_TYPE_QUESTIONS = 60
_TYPE_RANGES: dict[ExamTrack, range] = {
    ExamTrack.EGE: range(1, 35),
    ExamTrack.OGE: range(1, 20),
}


async def validate_homework_items(
    items: list[HomeworkItem],
    *,
    track: ExamTrack,
    teacher_id: uuid.UUID,
    settings: Settings,
    session: AsyncSession,
) -> None:
    """Reject invalid homework specs before persisting an assignment."""
    repo = _content_repo(track, settings)
    theme_repo = TeacherThemeRepository(session)
    for item in items:
        if isinstance(item, CustomThemeHomeworkItem):
            await _validate_custom_theme_item(item, teacher_id=teacher_id, theme_repo=theme_repo)
            continue
        if isinstance(item, TestByTypeItem):
            _validate_task_types(item.types, track=track)
            if item.variants is not None:
                _validate_variants_exist(item.variants, repo)
            _validate_test_by_type_questions(
                item.types,
                track=track,
                repo=repo,
                variants=item.variants,
            )
            continue
        if isinstance(item, TestPartialItem):
            _validate_task_types(item.types, track=track)
            _validate_variants_exist([item.variant], repo)
            _validate_questions_exist(
                item.types,
                track=track,
                repo=repo,
                variants=[item.variant],
            )
            continue
        if isinstance(item, TestVariantItem):
            _validate_variants_exist([item.variant], repo)
            _validate_variant_has_questions(item.variant, repo)


async def _validate_custom_theme_item(
    item: CustomThemeHomeworkItem,
    *,
    teacher_id: uuid.UUID,
    theme_repo: TeacherThemeRepository,
) -> None:
    theme = await theme_repo.get_for_teacher(item.theme_id, teacher_id)
    if theme is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Theme not found or not owned by teacher",
        )
    if item.task_ids is None:
        return
    tasks = await theme_repo.list_tasks(item.theme_id)
    known = {task.id for task in tasks}
    unknown = [task_id for task_id in item.task_ids if task_id not in known]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="task_ids must be a subset of theme tasks",
        )


def _validate_task_types(types: list[int], *, track: ExamTrack) -> None:
    allowed = _TYPE_RANGES[track]
    invalid = [type_num for type_num in types if type_num not in allowed]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Task type(s) {invalid} are out of range for track "
                f"{track.value} (allowed {allowed.start}–{allowed.stop - 1})"
            ),
        )


def _validate_questions_exist(
    types: list[int],
    *,
    track: ExamTrack,
    repo: ExamContentRepo,
    variants: list[str] | None,
) -> None:
    try:
        question_count = repo.count_expanded_questions(
            types,
            track=track,
            variants=variants,
        )
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


def _validate_test_by_type_questions(
    types: list[int],
    *,
    track: ExamTrack,
    repo: ExamContentRepo,
    variants: list[str] | None,
) -> None:
    try:
        question_count = repo.count_expanded_questions(
            types,
            track=track,
            variants=variants,
        )
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


def _validate_variant_has_questions(variant: str, repo: ExamContentRepo) -> None:
    try:
        questions = repo.list_questions(variant)
    except ContentDbError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Test content database unavailable",
        ) from exc
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No questions found for the requested variant",
        )


def _validate_variants_exist(variants: list[str], repo: ExamContentRepo) -> None:
    try:
        known = set(repo.list_variants())
    except ContentDbError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Test content database unavailable",
        ) from exc
    unknown = [variant for variant in variants if variant not in known]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown variant(s): {unknown}",
        )


def _content_repo(track: ExamTrack, settings: Settings) -> ExamContentRepo:
    path = (
        settings.content_ege_db_path
        if track == ExamTrack.EGE
        else settings.content_oge_db_path
    )
    return ExamContentRepo(path)
