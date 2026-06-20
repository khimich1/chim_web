"""Tutor agent long-term profile (PostgreSQL per user; Task 47 A7)."""

from __future__ import annotations

import uuid
from typing import Any

from app.services.tutor.context import get_tutor_context


def load_profile(user_id: str | None = None) -> dict[str, Any]:
    ctx = get_tutor_context()
    uid = user_id or ctx.user_id
    if ctx.profile_service is not None and ctx.run_async is not None:
        try:
            uuid.UUID(uid)
        except ValueError:
            return {}
        return ctx.run_async(ctx.profile_service.load())
    return {}


def update_profile(
    key: str,
    value: Any,
    user_id: str | None = None,
) -> dict[str, Any]:
    ctx = get_tutor_context()
    uid = user_id or ctx.user_id
    if ctx.profile_service is not None and ctx.run_async is not None:
        try:
            uuid.UUID(uid)
        except ValueError:
            return {}
        return ctx.run_async(
            ctx.profile_service.update_key(str(key), str(value)),
        )
    return {}
