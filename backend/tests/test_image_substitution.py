"""Unit tests for image placeholder substitution."""

from __future__ import annotations

from urllib.parse import quote

from app.services.image_substitution import (
    reference_answer_blocks_from_correct_ans,
    substitute_image_placeholders,
)


def test_replaces_ege_placeholder_with_image_url() -> None:
    filename = quote("рисунок0001.png")
    result = substitute_image_placeholders("См. [рисунок0001] ниже")
    assert result == f"См. /api/tests/images/{filename} ниже"


def test_leaves_text_without_placeholders_unchanged() -> None:
    text = "Обычный вопрос без рисунка"
    assert substitute_image_placeholders(text) == text


def test_reference_answer_blocks_text_only() -> None:
    blocks = reference_answer_blocks_from_correct_ans("Эталонный разбор")
    assert blocks == [{"type": "text", "content": "Эталонный разбор"}]


def test_reference_answer_blocks_with_answer_image() -> None:
    filename = quote("ответ0001.png")
    blocks = reference_answer_blocks_from_correct_ans(
        "Текст до\n[ответ0001]\nтекст после"
    )
    assert blocks[0] == {"type": "text", "content": "Текст до\n"}
    assert blocks[1] == {"type": "image", "url": f"/api/tests/images/{filename}"}
    assert blocks[2] == {"type": "text", "content": "\nтекст после"}
