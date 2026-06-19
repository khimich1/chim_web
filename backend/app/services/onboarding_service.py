"""Student onboarding state and welcome recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models import HomeworkStatus, StudentProfile, User
from app.repositories.app.activity_repo import ActivityRepository
from app.repositories.app.homework_repo import HomeworkRepository
from app.schemas.onboarding import (
    OnboardingChecklistRead,
    OnboardingPatch,
    OnboardingRead,
    OnboardingWelcomeRead,
    RecommendedActionRead,
)
from app.services.activity_service import ActivityService
from app.services.test_catalog_service import TestCatalogService

_DEFAULT_CHECKLIST: dict[str, bool] = {
    "login": False,
    "first_action": False,
    "lecture": False,
}


class OnboardingService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        activity: ActivityService | None = None,
    ) -> None:
        self._session = session
        self._homework = HomeworkRepository(session)
        self._catalog = TestCatalogService(settings)
        self._activity = activity or ActivityService(session)

    async def get_status(self, student: User) -> OnboardingRead:
        profile = await self._touch_first_login(student)
        return self._to_read(profile)

    async def get_welcome(self, student: User) -> OnboardingWelcomeRead:
        profile = await self._touch_first_login(student)
        await self._activity.record_onboarding_welcome_viewed(student.id)
        base = self._to_read(profile)
        recommended = await self._recommended_action(student)
        return OnboardingWelcomeRead(
            **base.model_dump(),
            recommended_action=recommended,
        )

    async def patch(self, student: User, data: OnboardingPatch) -> OnboardingRead:
        profile = await self._require_profile(student.id)
        checklist = _normalize_checklist(profile.onboarding_checklist)

        if data.mark_step is not None:
            checklist[data.mark_step] = True
            profile.onboarding_checklist = checklist
            await self._activity.record_onboarding_checklist_step(
                student.id,
                data.mark_step,
            )
            if data.mark_step == "first_action":
                await self._activity.record_onboarding_first_action(
                    student.id,
                    "checklist",
                )

        if data.complete_welcome:
            checklist["login"] = True
            profile.onboarding_checklist = checklist
            if profile.onboarding_completed_at is None:
                profile.onboarding_completed_at = datetime.now(timezone.utc)
            if data.mark_step == "first_action":
                await self._activity.record_onboarding_welcome_completed(
                    student.id,
                )
            else:
                await self._activity.record_onboarding_welcome_skipped(
                    student.id,
                )

        await self._session.flush()
        return self._to_read(profile)

    async def mark_first_action(
        self,
        student_id: uuid.UUID,
        *,
        action_type: str = "unknown",
    ) -> None:
        profile = await self._require_profile(student_id)
        checklist = _normalize_checklist(profile.onboarding_checklist)
        if checklist.get("first_action"):
            await self._activity.record_onboarding_first_action(
                student_id,
                action_type,
            )
            return
        checklist["first_action"] = True
        profile.onboarding_checklist = checklist
        await self._activity.record_onboarding_first_action(student_id, action_type)
        await self._session.flush()

    async def _touch_first_login(self, student: User) -> StudentProfile:
        profile = await self._require_profile(student.id)
        checklist = _normalize_checklist(profile.onboarding_checklist)
        changed = False

        if profile.first_login_at is None:
            profile.first_login_at = datetime.now(timezone.utc)
            changed = True

        if not checklist.get("login"):
            checklist["login"] = True
            profile.onboarding_checklist = checklist
            changed = True

        if changed:
            await self._session.flush()

        return profile

    async def _recommended_action(self, student: User) -> RecommendedActionRead:
        assignments = await self._homework.list_by_student(student.id)
        active = next(
            (
                item
                for item in assignments
                if item.status in (HomeworkStatus.ASSIGNED, HomeworkStatus.IN_PROGRESS)
            ),
            None,
        )
        if active is not None:
            return RecommendedActionRead(
                kind="homework",
                label=f"Открыть задание: {active.title}",
                homework_id=str(active.id),
            )

        track = await self._catalog.resolve_track(self._session, student)
        variants = self._catalog.list_variants(track)
        if variants:
            first = variants[0]
            return RecommendedActionRead(
                kind="diagnostic_test",
                label="Начать диагностический тест",
                variant_ref=first.filename,
            )

        return RecommendedActionRead(
            kind="textbook",
            label="Открыть учебник",
            textbook_topic=None,
        )

    async def _require_profile(self, student_id: uuid.UUID) -> StudentProfile:
        profile = await self._session.scalar(
            select(StudentProfile).where(StudentProfile.user_id == student_id)
        )
        if profile is None:
            raise ValueError(f"Student profile not found for user {student_id}")
        return profile

    def _to_read(self, profile: StudentProfile) -> OnboardingRead:
        checklist = OnboardingChecklistRead.model_validate(
            _normalize_checklist(profile.onboarding_checklist)
        )
        return OnboardingRead(
            first_login_at=profile.first_login_at,
            onboarding_completed_at=profile.onboarding_completed_at,
            checklist=checklist,
            needs_welcome=profile.onboarding_completed_at is None,
        )


def _normalize_checklist(raw: dict[str, Any] | None) -> dict[str, bool]:
    base = dict(_DEFAULT_CHECKLIST)
    if raw:
        for key in base:
            if key in raw:
                base[key] = bool(raw[key])
    return base


def is_student_activated(
    profile: StudentProfile,
    *,
    has_learning_activity: bool = False,
) -> bool:
    checklist = _normalize_checklist(profile.onboarding_checklist)
    return bool(checklist.get("first_action")) or has_learning_activity


async def resolve_students_activation(
    session: AsyncSession,
    profiles: list[StudentProfile],
) -> dict[uuid.UUID, bool]:
    """Batch activation lookup for teacher student list."""
    if not profiles:
        return {}
    repo = ActivityRepository(session)
    active_ids = await repo.list_student_ids_with_learning_activity(
        [profile.user_id for profile in profiles],
    )
    return {
        profile.user_id: is_student_activated(
            profile,
            has_learning_activity=profile.user_id in active_ids,
        )
        for profile in profiles
    }
