"""Shared enumerations for app DB models."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class ExamTrack(str, enum.Enum):
    EGE = "ege"
    OGE = "oge"


class TestSessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class StepStatus(str, enum.Enum):
    UNSEEN = "unseen"
    ANSWERED = "answered"
    CHECKED = "checked"


class HomeworkStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"


class HomeworkItemKind(str, enum.Enum):
    LECTURE = "lecture"
    TEST_VARIANT = "test_variant"
    TEST_PARTIAL = "test_partial"
    TEST_BY_TYPE = "test_by_type"


class NotificationType(str, enum.Enum):
    HOMEWORK_SUBMITTED = "homework_submitted"


class TutorMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ActivityEventType(str, enum.Enum):
    STEP_CORRECT = "step_correct"
    HOMEWORK_COMPLETE = "homework_complete"
    STREAK_DAILY = "streak_daily"
    STREAK_WEEKLY = "streak_weekly"
    ONBOARDING_WELCOME_VIEWED = "onboarding_welcome_viewed"
    ONBOARDING_WELCOME_COMPLETED = "onboarding_welcome_completed"
    ONBOARDING_WELCOME_SKIPPED = "onboarding_welcome_skipped"
    ONBOARDING_CHECKLIST_STEP = "onboarding_checklist_step"
    ONBOARDING_FIRST_ACTION = "onboarding_first_action"
