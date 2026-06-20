"""Onboarding request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

OnboardingStep = Literal["login", "first_action", "lecture"]


class OnboardingChecklistRead(BaseModel):
    login: bool = False
    first_action: bool = False
    lecture: bool = False


class OnboardingRead(BaseModel):
    first_login_at: datetime | None
    onboarding_completed_at: datetime | None
    checklist: OnboardingChecklistRead
    needs_welcome: bool


class OnboardingPatch(BaseModel):
    complete_welcome: bool = False
    mark_step: OnboardingStep | None = None


class RecommendedActionRead(BaseModel):
    """Suggested first action for the welcome screen."""

    model_config = ConfigDict(from_attributes=True)

    kind: Literal["homework", "diagnostic_test", "textbook"]
    label: str
    homework_id: str | None = None
    variant_ref: str | None = None
    textbook_topic: str | None = None


class OnboardingWelcomeRead(OnboardingRead):
    recommended_action: RecommendedActionRead
