"""Test session adapters package (Task 97)."""

from app.services.test_session.common import (
    answer_image_url,
    session_duration_minutes,
)
from app.services.test_session.custom_adapter import CustomSessionAdapter
from app.services.test_session.exam_adapter import ExamSessionAdapter
from app.services.test_session.facade import TestSessionService
from app.services.test_session.homework_adapter import HomeworkSessionAdapter

# Backward-compatible alias for unit tests and legacy imports.
_session_duration_minutes = session_duration_minutes

__all__ = [
    "CustomSessionAdapter",
    "ExamSessionAdapter",
    "HomeworkSessionAdapter",
    "TestSessionService",
    "answer_image_url",
    "session_duration_minutes",
]
