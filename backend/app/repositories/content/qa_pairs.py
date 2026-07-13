"""Parse lecture self-check Q/A JSON fields from prepared_lectures."""

from __future__ import annotations

import json


def parse_qa_pairs(
    qa_questions: str | None,
    qa_answers: str | None,
) -> list[tuple[str, str]]:
    if not qa_questions or not qa_answers:
        return []
    try:
        questions = json.loads(qa_questions)
        answers = json.loads(qa_answers)
    except json.JSONDecodeError:
        return []
    if not isinstance(questions, list) or not isinstance(answers, list):
        return []
    pairs: list[tuple[str, str]] = []
    for question, answer in zip(questions, answers, strict=False):
        if (
            isinstance(question, str)
            and isinstance(answer, str)
            and question.strip()
            and answer.strip()
        ):
            pairs.append((question.strip(), answer.strip()))
    return pairs
