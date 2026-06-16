"""Answer grading for test questions (v1: exact match after normalization)."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


class GradingService:
    """Compare student answers to `correct_ans` using normalized exact match."""

    @staticmethod
    def normalize_answer(answer: str) -> str:
        """Trim, remove whitespace, fold case for comparison."""
        text = answer.strip()
        text = re.sub(r"\s+", "", text)
        return text.casefold()

    def grade(self, student_answer: str, correct_ans: str) -> bool:
        normalized_student = self.normalize_answer(student_answer)
        normalized_correct = self.normalize_answer(correct_ans)
        is_correct = normalized_student == normalized_correct
        if not is_correct:
            logger.info(
                "answer_mismatch student=%r correct=%r",
                normalized_student,
                normalized_correct,
            )
        return is_correct
