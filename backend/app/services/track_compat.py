"""Track compatibility checks for homework template assign (MVP).

If a test item references a variant that exists only in one exam track DB,
assigning it to a student on the other track is rejected with 422.
``lecture`` / ``custom_theme`` items do not participate.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.core.config import Settings
from app.models.enums import ExamTrack
from app.repositories.content.base import ContentDbError
from app.repositories.content.tests import ExamContentRepo
from app.schemas.homework import (
    HomeworkItem,
    TestByTypeItem,
    TestPartialItem,
    TestVariantItem,
)


def assert_items_compatible_with_track(
    items: list[HomeworkItem],
    *,
    student_track: ExamTrack,
    settings: Settings,
) -> None:
    """Raise 422 when a test item is bound to a track other than the student's."""
    try:
        ege_variants = set(ExamContentRepo(settings.content_ege_db_path).list_variants())
        oge_variants = set(ExamContentRepo(settings.content_oge_db_path).list_variants())
    except ContentDbError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Test content database unavailable",
        ) from exc

    for item in items:
        for variant in _variants_from_item(item):
            in_ege = variant in ege_variants
            in_oge = variant in oge_variants
            if in_ege and not in_oge and student_track != ExamTrack.EGE:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Template item uses EGE variant {variant!r}, "
                        f"incompatible with student track {student_track.value}"
                    ),
                )
            if in_oge and not in_ege and student_track != ExamTrack.OGE:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(
                        f"Template item uses OGE variant {variant!r}, "
                        f"incompatible with student track {student_track.value}"
                    ),
                )


def _variants_from_item(item: HomeworkItem) -> list[str]:
    if isinstance(item, TestVariantItem | TestPartialItem):
        return [item.variant]
    if isinstance(item, TestByTypeItem) and item.variants:
        return list(item.variants)
    return []
