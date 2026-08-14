"""Marketing lead submission — forward to Google Sheets Apps Script webhook."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import Settings
from app.schemas.leads import LeadCreate, LeadCreated

logger = logging.getLogger(__name__)

_GOAL_LABELS = {
    "ege": "ЕГЭ",
    "oge": "ОГЭ",
    "school": "Школа",
}


class LeadService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def submit(self, body: LeadCreate, *, client_ip: str | None = None) -> LeadCreated:
        lead_id = uuid.uuid4()
        row = self._build_row(body, lead_id=lead_id, client_ip=client_ip)
        await self._forward_to_webhook(lead_id, row)
        return LeadCreated(id=lead_id)

    def _build_row(
        self,
        body: LeadCreate,
        *,
        lead_id: uuid.UUID,
        client_ip: str | None,
    ) -> dict[str, Any]:
        notes_parts: list[str] = []
        if body.comment:
            notes_parts.append(body.comment.strip())
        if body.utm_medium:
            notes_parts.append(f"utm_medium={body.utm_medium}")
        if client_ip:
            notes_parts.append(f"ip={client_ip}")

        return {
            "lead_id": str(lead_id),
            "date": datetime.now(UTC).isoformat(),
            "name": body.name.strip(),
            "contact": body.phone,
            "class": body.school_class,
            "exam": _GOAL_LABELS[body.goal],
            "source": body.source_page,
            "utm_source": body.utm_source or "",
            "utm_campaign": body.utm_campaign or "",
            "notes": " · ".join(notes_parts),
        }

    async def _forward_to_webhook(self, lead_id: uuid.UUID, row: dict[str, Any]) -> None:
        webhook_url = self._settings.google_sheets_webhook_url
        if not webhook_url:
            logger.warning(
                "lead_webhook_skipped",
                extra={"lead_id": str(lead_id), "reason": "GOOGLE_SHEETS_WEBHOOK_URL not set"},
            )
            return

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=row)
                response.raise_for_status()
        except Exception as exc:
            logger.error(
                "lead_webhook_failed",
                extra={
                    "lead_id": str(lead_id),
                    "payload": row,
                    "error": str(exc),
                },
            )
