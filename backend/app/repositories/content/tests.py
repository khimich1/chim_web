"""Read-only repository for test_ege.db / test_oge.db."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.repositories.content.base import open_readonly


@dataclass(frozen=True, slots=True)
class TestQuestion:
    id: int
    filename: str
    type: int
    question: str
    options: str | None
    correct_ans: str
    hint: str | None
    detailed_explanation: str | None


class ExamContentRepo:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def list_variants(self) -> list[str]:
        with open_readonly(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT filename
                FROM tests
                WHERE COALESCE(has_issue, 0) = 0
                  AND filename NOT IN (SELECT filename FROM tests_bug)
                ORDER BY filename
                """
            ).fetchall()
        return [row["filename"] for row in rows]

    def list_questions(self, filename: str) -> list[TestQuestion]:
        with open_readonly(self._db_path) as conn:
            rows = conn.execute(
                """
                SELECT t.rowid AS id, t.filename, t.type, t.question, t.options,
                       t.correct_ans, t.hint, t.detailed_explanation
                FROM tests t
                WHERE t.filename = ?
                  AND COALESCE(t.has_issue, 0) = 0
                  AND t.filename NOT IN (SELECT filename FROM tests_bug)
                ORDER BY t.type
                """,
                (filename,),
            ).fetchall()

        return [
            TestQuestion(
                id=row["id"],
                filename=row["filename"],
                type=row["type"],
                question=row["question"],
                options=row["options"],
                correct_ans=row["correct_ans"],
                hint=row["hint"],
                detailed_explanation=row["detailed_explanation"],
            )
            for row in rows
        ]
