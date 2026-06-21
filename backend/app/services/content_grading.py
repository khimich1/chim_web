"""Grading mode for exam content by track and task type (SPEC §1.10, Task 87)."""

from __future__ import annotations

from typing import Literal

from app.models import TestSessionStep
from app.models.enums import ExamTrack, GradingMode, StepStatus

ContentGradingMode = Literal["exact", "self_check"]


def get_content_grading_mode(track: ExamTrack, task_type: int) -> ContentGradingMode:
    """Return grading mode for a task from read-only exam content DB."""
    if track == ExamTrack.OGE:
        return "exact"
    if track == ExamTrack.EGE:
        if 1 <= task_type <= 28:
            return "exact"
        if 29 <= task_type <= 34:
            return "self_check"
    return "exact"


def step_grading_mode_for_exam(track: ExamTrack, task_type: int) -> GradingMode | None:
    """Map exam content grading to StepRead grading_mode (None = «Проверить»)."""
    if get_content_grading_mode(track, task_type) == "self_check":
        return GradingMode.SELF_CHECK
    return None


def exam_step_score_parts(
    track: ExamTrack,
    task_type: int,
    step: TestSessionStep,
) -> tuple[int, int]:
    """Return (max_points, score_points) for one exam step (§1.10 PO decision)."""
    if get_content_grading_mode(track, task_type) == "self_check":
        max_points = 1
        score_points = 1 if step.status == StepStatus.CHECKED else 0
        return max_points, score_points
    max_points = 1
    score_points = 1 if step.is_correct else 0
    return max_points, score_points
