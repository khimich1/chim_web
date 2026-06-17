"""Deterministic validation for tutor solve-pipeline drafts (§17.4)."""

from __future__ import annotations

import re
from typing import Literal

AnswerFormat = Literal["digit_string", "number"]

_NUMBER_PATTERN = re.compile(
    r"[-+]?\d+(?:[.,]\d+)?(?:[eE][-+]?\d+)?"
)
_ANSWER_LABEL_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:"
    r"(?:итог(?:овый)?|ответ|результат|ключ)"
    r"(?:\s+ответ)?"
    r")\s*[:\-—]\s*(.+)$",
    re.IGNORECASE | re.MULTILINE,
)
_CORRESPONDENCE_LINE = re.compile(
    r"^\s*([А-ГA-Dа-гa-d])\s*[→\->:]\s*(.+)$",
    re.MULTILINE,
)

_NUMBER_TASK_TYPES = frozenset({26, 27, 28})
_DIGIT_STRING_TASK_TYPES = frozenset({*range(1, 7), *range(9, 25), 7, 8})


def detect_answer_format(task_type: int, correct_ans: str) -> AnswerFormat:
    """Pick comparison mode from task type and reference key."""
    if task_type in _NUMBER_TASK_TYPES:
        return "number"
    if task_type in _DIGIT_STRING_TASK_TYPES:
        return "digit_string"
    if _NUMBER_PATTERN.search(correct_ans.replace(" ", "")):
        return "number"
    return "digit_string"


def normalize_digit_string(value: str) -> str:
    """Normalize digit-string keys (order preserved, separators removed)."""
    text = value.strip().casefold()
    text = re.sub(r"[\s,;|/\\\-–—]+", "", text)
    return text


def normalize_number(value: str) -> float | None:
    """Parse a numeric answer; strip units and normalize decimal separator."""
    text = value.strip().casefold()
    text = text.replace(",", ".")
    match = _NUMBER_PATTERN.search(text)
    if match is None:
        return None
    token = match.group(0).replace(",", ".")
    try:
        return float(token)
    except ValueError:
        return None


def numbers_equal(
    student: str,
    correct: str,
    *,
    rel_tol: float = 1e-4,
    abs_tol: float = 1e-6,
) -> bool:
    left = normalize_number(student)
    right = normalize_number(correct)
    if left is None or right is None:
        return False
    return abs(left - right) <= max(rel_tol * max(abs(left), abs(right)), abs_tol)


def keys_match(student_key: str, correct_ans: str, answer_format: AnswerFormat) -> bool:
    if answer_format == "number":
        return numbers_equal(student_key, correct_ans)
    return normalize_digit_string(student_key) == normalize_digit_string(correct_ans)


def extract_answer_key(draft: str, answer_format: AnswerFormat) -> str | None:
    """Best-effort extraction of the final key from a solver draft."""
    labeled = _ANSWER_LABEL_PATTERN.findall(draft)
    if labeled:
        return labeled[-1].strip()

    lines = [line.strip() for line in draft.splitlines() if line.strip()]
    for line in reversed(lines):
        if answer_format == "number":
            if _NUMBER_PATTERN.search(line):
                return line
        else:
            compact = re.sub(r"[\s,;|/\\\-–—]+", "", line)
            if compact and compact.isdigit():
                return compact
            if re.fullmatch(r"[1-4]+", compact):
                return compact

    if answer_format == "number":
        matches = _NUMBER_PATTERN.findall(draft.replace(",", "."))
        return matches[-1] if matches else None

    digits = re.findall(r"\d", draft)
    return "".join(digits[-4:]) if digits else None


def has_theory_citation(draft: str, theory_hits: list[dict]) -> bool:
    """True if draft mentions at least one topic or chunk_title from theory hits."""
    lowered = draft.casefold()
    for hit in theory_hits:
        topic = str(hit.get("topic") or "").strip()
        chunk_title = str(hit.get("chunk_title") or "").strip()
        if topic and topic.casefold() in lowered:
            return True
        if chunk_title and chunk_title.casefold() in lowered:
            return True
    return False


def correspondence_consistent(draft: str, correct_ans: str) -> bool:
    """For types 7/8: mapped letters must match digit key positions."""
    key = normalize_digit_string(correct_ans)
    if not key:
        return True

    mappings: list[str] = []
    for match in _CORRESPONDENCE_LINE.finditer(draft):
        letter = match.group(1).upper()
        idx = ord(letter) - ord("A") if letter in "ABCD" else ord(letter) - ord("А")
        if idx < 0 or idx >= len(key):
            continue
        digit = key[idx]
        tail = match.group(2)
        if digit not in normalize_digit_string(tail):
            return False
        mappings.append(digit)

    if not mappings:
        return True
    return "".join(mappings) == key[: len(mappings)]


def question_fragments_present(draft: str, question: str, *, min_len: int = 12) -> bool:
    """Check that a substantive fragment of the DB question appears in the draft."""
    normalized_question = re.sub(r"\s+", " ", question.strip())
    if len(normalized_question) < min_len:
        return normalized_question.casefold() in draft.casefold()

    fragment = normalized_question[: min(len(normalized_question), 40)].strip()
    return fragment.casefold() in draft.casefold()


def validate_draft(
    draft: str,
    *,
    correct_ans: str,
    answer_format: AnswerFormat,
    theory_hits: list[dict],
    question: str,
    task_type: int | None = None,
) -> list[str]:
    """Run deterministic critic checks; return human-readable issues."""
    issues: list[str] = []

    extracted = extract_answer_key(draft, answer_format)
    if extracted is None:
        issues.append("не удалось извлечь итоговый ключ из ответа")
    elif not keys_match(extracted, correct_ans, answer_format):
        issues.append(f"ключ {extracted!r} ≠ correct_ans {correct_ans!r}")

    if not has_theory_citation(draft, theory_hits):
        issues.append("нет ссылки на учебник")

    if question and not question_fragments_present(draft, question):
        issues.append("условие не из БД")

    if task_type in {7, 8} and not correspondence_consistent(draft, correct_ans):
        issues.append("разбор противоречит ключу")

    return issues
