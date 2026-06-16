"""Read-only SQLite content repositories."""

from app.repositories.content.lectures import LectureContentRepo
from app.repositories.content.tests import ExamContentRepo

__all__ = ["ExamContentRepo", "LectureContentRepo"]
