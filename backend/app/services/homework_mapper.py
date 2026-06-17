"""Shared ORM → schema mapping for homework.

Lives in its own module so both ``HomeworkService`` and
``HomeworkSubmitService`` can build a ``HomeworkRead`` without importing a
private helper across service boundaries.
"""

from __future__ import annotations

import uuid

from app.models import HomeworkAssignment
from app.schemas.homework import (
    HomeworkItemProgressRead,
    HomeworkRead,
    HomeworkSubmissionRead,
)


def to_homework_read(
    assignment: HomeworkAssignment,
    *,
    include_student_email: bool = False,
    active_test_session_id: uuid.UUID | None = None,
) -> HomeworkRead:
    submission = None
    if assignment.submission is not None:
        submission = HomeworkSubmissionRead.model_validate(assignment.submission)

    progress = [
        HomeworkItemProgressRead.model_validate(row)
        for row in assignment.item_progress
    ]

    return HomeworkRead(
        id=assignment.id,
        student_id=assignment.student_id,
        student_email=assignment.student.email if include_student_email else None,
        title=assignment.title,
        description=assignment.description,
        due_at=assignment.due_at,
        items=assignment.items,
        status=assignment.status,
        created_at=assignment.created_at,
        submission=submission,
        progress=progress,
        active_test_session_id=active_test_session_id,
    )
