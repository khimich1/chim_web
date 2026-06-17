"""Unit tests for solve-pipeline validation helpers."""

from __future__ import annotations

from app.services.tutor.validation import (
    correspondence_consistent,
    detect_answer_format,
    extract_answer_key,
    has_theory_citation,
    keys_match,
    normalize_digit_string,
    normalize_number,
    numbers_equal,
    validate_draft,
)


def test_normalize_digit_string_preserves_order() -> None:
    assert normalize_digit_string("1 2 3 4") == "1234"
    assert normalize_digit_string("1,2;3|4") == "1234"


def test_normalize_number_strips_units() -> None:
    assert normalize_number("3,35 моль") == 3.35
    assert normalize_number("0.5 г") == 0.5


def test_numbers_equal_with_comma_and_units() -> None:
    assert numbers_equal("3,35 моль", "3.35")
    assert not numbers_equal("3,34", "3.35")


def test_keys_match_digit_string_no_reorder() -> None:
    assert keys_match("1 2 3", "123", "digit_string")
    assert not keys_match("3 2 1", "123", "digit_string")


def test_detect_answer_format_by_task_type() -> None:
    assert detect_answer_format(26, "3.5") == "number"
    assert detect_answer_format(15, "1234") == "digit_string"


def test_extract_answer_key_from_labeled_line() -> None:
    draft = "Разбор...\n\nОтвет: 1234"
    assert extract_answer_key(draft, "digit_string") == "1234"


def test_has_theory_citation_requires_topic_or_chunk() -> None:
    hits = [{"topic": "Алканы", "chunk_title": "Свойства"}]
    assert has_theory_citation("Согласно разделу «Свойства»...", hits)
    assert not has_theory_citation("Ответ без ссылок", hits)


def test_correspondence_consistent_for_type_7() -> None:
    draft = "А → вариант 1\nБ → вариант 2\nОтвет: 12"
    assert correspondence_consistent(draft, "12")
    assert not correspondence_consistent("А → 2\nБ → 1", "12")


def test_validate_draft_reports_key_and_citation_issues() -> None:
    issues = validate_draft(
        "Краткий ответ без источника.\nОтвет: 99",
        correct_ans="12",
        answer_format="digit_string",
        theory_hits=[{"topic": "Соли", "chunk_title": "Введение"}],
        question="EGE question about salts",
        task_type=15,
    )
    assert any("ключ" in issue for issue in issues)
    assert any("учебник" in issue for issue in issues)


def test_validate_draft_passes_good_draft() -> None:
    issues = validate_draft(
        (
            "EGE question about salts\n"
            "По теме «Соли — Введение»...\n"
            "Ответ: secret-answer"
        ),
        correct_ans="secret-answer",
        answer_format="digit_string",
        theory_hits=[{"topic": "Соли", "chunk_title": "Введение"}],
        question="EGE question about salts",
        task_type=15,
    )
    assert issues == []
