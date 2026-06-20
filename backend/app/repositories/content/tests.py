"""Read-only repository for test_ege.db / test_oge.db."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.enums import ExamTrack
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

    def list_task_types(self) -> list[int]:
        """Distinct task type numbers available across exam variants."""
        variants = self.list_variants()
        if not variants:
            return []
        placeholders = ",".join("?" * len(variants))
        with open_readonly(self._db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT DISTINCT t.type
                FROM tests t
                WHERE t.filename IN ({placeholders})
                  AND COALESCE(t.has_issue, 0) = 0
                  AND t.filename NOT IN (SELECT filename FROM tests_bug)
                ORDER BY t.type
                """,
                variants,
            ).fetchall()
        return [int(row["type"]) for row in rows]

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

    def expand_types_across_variants(
        self,
        types: list[int],
        *,
        track: ExamTrack,
        variants: list[str] | None = None,
    ) -> list[tuple[str, list[int] | None]]:
        """Expand homework ``test_by_type`` items into (variant, types) sources.

        EGE: one question per variant for each requested ``type``.
        OGE: full file ``{type:03d}.txt`` (all variants of that task type).
        When ``variants`` is set, only those files are included (SPEC §1.9.4).
        """
        all_variants = self.list_variants()
        selected = all_variants if variants is None else list(variants)

        if track == ExamTrack.OGE:
            sources: list[tuple[str, list[int] | None]] = []
            known_variants = set(all_variants)
            for type_num in sorted(types):
                filename = f"{type_num:03d}.txt"
                if filename in known_variants and filename in selected:
                    sources.append((filename, None))
            return sources

        sources = []
        for type_num in sorted(types):
            for variant in selected:
                if self._variant_has_type(variant, type_num):
                    sources.append((variant, [type_num]))
        return sources

    def count_expanded_questions(
        self,
        types: list[int],
        *,
        track: ExamTrack,
        variants: list[str] | None = None,
    ) -> int:
        """Count questions that ``test_by_type`` would include (for validation)."""
        total = 0
        for variant, type_filter in self.expand_types_across_variants(
            types, track=track, variants=variants
        ):
            questions = self.list_questions(variant)
            if type_filter is not None:
                wanted = set(type_filter)
                questions = [question for question in questions if question.type in wanted]
            total += len(questions)
        return total

    def _variant_has_type(self, variant: str, type_num: int) -> bool:
        return any(question.type == type_num for question in self.list_questions(variant))

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

    def get_question(self, test_id: int) -> TestQuestion | None:
        """Fetch a single question by rowid (includes correct_ans / hint)."""
        with open_readonly(self._db_path) as conn:
            row = conn.execute(
                """
                SELECT t.rowid AS id, t.filename, t.type, t.question, t.options,
                       t.correct_ans, t.hint, t.detailed_explanation
                FROM tests t
                WHERE t.rowid = ?
                  AND COALESCE(t.has_issue, 0) = 0
                  AND t.filename NOT IN (SELECT filename FROM tests_bug)
                """,
                (test_id,),
            ).fetchone()
        if row is None:
            return None
        return TestQuestion(
            id=row["id"],
            filename=row["filename"],
            type=row["type"],
            question=row["question"],
            options=row["options"],
            correct_ans=row["correct_ans"],
            hint=row["hint"],
            detailed_explanation=row["detailed_explanation"],
        )

    def get_image(self, filename: str) -> bytes | None:
        with open_readonly(self._db_path) as conn:
            row = conn.execute(
                "SELECT data FROM images WHERE filename = ?",
                (filename,),
            ).fetchone()
        if row is None:
            return None
        return row["data"]

    def search_questions(
        self,
        *,
        query: str | None = None,
        task_type: int | None = None,
        limit: int = 5,
    ) -> list[TestQuestion]:
        """Search questions by substring and/or task type (excludes has_issue)."""
        clauses = [
            "COALESCE(t.has_issue, 0) = 0",
            "t.filename NOT IN (SELECT filename FROM tests_bug)",
        ]
        params: list[object] = []

        if task_type is not None:
            clauses.append("t.type = ?")
            params.append(task_type)
        if query:
            clauses.append("t.question LIKE ?")
            params.append(f"%{query}%")

        sql = f"""
            SELECT t.rowid AS id, t.filename, t.type, t.question, t.options,
                   t.correct_ans, t.hint, t.detailed_explanation
            FROM tests t
            WHERE {" AND ".join(clauses)}
            ORDER BY t.rowid
            LIMIT ?
        """
        params.append(max(1, limit))

        with open_readonly(self._db_path) as conn:
            rows = conn.execute(sql, params).fetchall()

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
