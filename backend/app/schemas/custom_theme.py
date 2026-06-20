"""Student-facing schemas for published custom themes (SPEC §1.9)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class CustomThemeListItem(BaseModel):
    """Published theme visible to a student on GET /api/custom-themes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str | None = None
    task_count: int
    sort_order: int
