"""Unit tests for GradingService (exact match after normalization)."""

from __future__ import annotations

import pytest

from app.services.grading_service import GradingService


@pytest.fixture
def grading() -> GradingService:
    return GradingService()


def test_accepts_exact_match(grading: GradingService) -> None:
    assert grading.grade("23", "23") is True


def test_accepts_answer_with_extra_whitespace(grading: GradingService) -> None:
    assert grading.grade(" 422 ", "422") is True
    assert grading.grade("4 2 2", "422") is True


def test_rejects_wrong_answer(grading: GradingService) -> None:
    assert grading.grade("24", "23") is False


def test_rejects_empty_answer(grading: GradingService) -> None:
    assert grading.grade("", "23") is False
    assert grading.grade("   ", "23") is False


def test_case_insensitive_for_letters(grading: GradingService) -> None:
    assert grading.grade("Ab", "ab") is True


def test_normalize_strips_and_collapses(grading: GradingService) -> None:
    assert GradingService.normalize_answer("  1 2 3  ") == "123"
