"""Custom theme test session logic — backward-compatible re-export (Task 97).

Prefer `CustomSessionAdapter` from `app.services.test_session`.
"""

from app.services.test_session.common import answer_image_url, session_duration_minutes
from app.services.test_session.custom_adapter import CustomSessionAdapter

CustomTestSessionService = CustomSessionAdapter

# Legacy private aliases used by homework_service and test_session adapters.
_answer_image_url = answer_image_url
_session_duration_minutes = session_duration_minutes

__all__ = [
    "CustomSessionAdapter",
    "CustomTestSessionService",
    "_answer_image_url",
    "_session_duration_minutes",
]
