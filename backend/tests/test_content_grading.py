"""Tests for content grading mode helper (Task 87)."""

from app.models.enums import ExamTrack
from app.services.content_grading import get_content_grading_mode


def test_ege_exact_for_types_1_to_28() -> None:
    assert get_content_grading_mode(ExamTrack.EGE, 1) == "exact"
    assert get_content_grading_mode(ExamTrack.EGE, 28) == "exact"


def test_ege_self_check_for_types_29_to_34() -> None:
    assert get_content_grading_mode(ExamTrack.EGE, 29) == "self_check"
    assert get_content_grading_mode(ExamTrack.EGE, 34) == "self_check"


def test_oge_always_exact() -> None:
    assert get_content_grading_mode(ExamTrack.OGE, 1) == "exact"
    assert get_content_grading_mode(ExamTrack.OGE, 19) == "exact"


def test_unknown_type_falls_back_to_exact() -> None:
    assert get_content_grading_mode(ExamTrack.EGE, 0) == "exact"
    assert get_content_grading_mode(ExamTrack.EGE, 99) == "exact"


def test_step_grading_mode_for_exam() -> None:
    from app.models.enums import GradingMode
    from app.services.content_grading import step_grading_mode_for_exam

    assert step_grading_mode_for_exam(ExamTrack.EGE, 28) is None
    assert step_grading_mode_for_exam(ExamTrack.EGE, 29) == GradingMode.SELF_CHECK


def test_exam_step_score_parts_exact() -> None:
    from app.models.enums import StepStatus
    from app.models.test_session import TestSessionStep
    from app.services.content_grading import exam_step_score_parts

    step = TestSessionStep(
        position=0,
        test_id=1,
        status=StepStatus.CHECKED,
        is_correct=True,
        hint_used=False,
    )
    assert exam_step_score_parts(ExamTrack.EGE, 1, step) == (1, 1)

    step_wrong = TestSessionStep(
        position=0,
        test_id=1,
        status=StepStatus.CHECKED,
        is_correct=False,
        hint_used=False,
    )
    assert exam_step_score_parts(ExamTrack.EGE, 1, step_wrong) == (1, 0)


def test_exam_step_score_parts_self_check() -> None:
    from app.models.enums import StepStatus
    from app.models.test_session import TestSessionStep
    from app.services.content_grading import exam_step_score_parts

    unchecked = TestSessionStep(
        position=0,
        test_id=1,
        status=StepStatus.UNSEEN,
        is_correct=None,
        hint_used=False,
    )
    assert exam_step_score_parts(ExamTrack.EGE, 29, unchecked) == (1, 0)

    checked = TestSessionStep(
        position=0,
        test_id=1,
        status=StepStatus.CHECKED,
        is_correct=None,
        hint_used=False,
    )
    assert exam_step_score_parts(ExamTrack.EGE, 29, checked) == (1, 1)
