"""Unit tests for image placeholder substitution."""

from __future__ import annotations

from urllib.parse import quote

from app.services.image_substitution import substitute_image_placeholders


def test_replaces_ege_placeholder_with_image_url() -> None:
    filename = quote("рисунок0001.png")
    result = substitute_image_placeholders("См. [рисунок0001] ниже")
    assert result == f"См. /api/tests/images/{filename} ниже"


def test_leaves_text_without_placeholders_unchanged() -> None:
    text = "Обычный вопрос без рисунка"
    assert substitute_image_placeholders(text) == text
