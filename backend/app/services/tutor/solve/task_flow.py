"""Task-id extraction and theory query helpers for solve-pipeline."""

from __future__ import annotations

import re

_TASK_ID_PATTERN = re.compile(
    r"(?:"
    r"задани[ея]|задач(?:а|у|е|и|ей|ью)|задачк[ау]"
    r")"
    r"[\s№#]*(\d+)",
    re.IGNORECASE,
)
_ALT_TASK_PATTERN = re.compile(
    r"(?:разбер[иь]|объясни|помоги\s+с)\s+(?:с\s+)?(?:задани[емя]|задач[ейю])\s*№?\s*(\d+)",
    re.IGNORECASE,
)


def extract_task_id(text: str) -> int | None:
    """Extract task bank id from a user message."""
    for pattern in (_TASK_ID_PATTERN, _ALT_TASK_PATTERN):
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def build_theory_query(question: str, *, max_words: int = 12) -> str:
    """Build a compact RAG query from the task statement."""
    cleaned = re.sub(r"\s+", " ", question.strip())
    if not cleaned:
        return "химия"
    words = cleaned.split()
    if len(words) <= max_words:
        return cleaned
    return " ".join(words[:max_words])
