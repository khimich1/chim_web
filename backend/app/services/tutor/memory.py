"""Tutor agent long-term profile (JSON file per user; Task 33 → PostgreSQL)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services.tutor.context import get_tutor_context


def _profile_path(user_id: str | None = None) -> Path:
    ctx = get_tutor_context()
    uid = user_id or ctx.user_id
    settings = get_settings()
    settings.tutor_profile_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in uid)
    return settings.tutor_profile_dir / f"{safe_id}.json"


def load_profile(user_id: str | None = None) -> dict[str, Any]:
    path = _profile_path(user_id)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def update_profile(key: str, value: Any, user_id: str | None = None) -> dict[str, Any]:
    path = _profile_path(user_id)
    profile = load_profile(user_id)
    profile[str(key)] = value
    path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return profile
