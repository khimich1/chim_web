"""Replace image placeholders in test question text with API image URLs."""

from __future__ import annotations

import re
from urllib.parse import quote

# Matches [рисунок0001], [рисунок0002], …
_IMAGE_PLACEHOLDER_RE = re.compile(r"\[рисунок(\d+)\]", re.IGNORECASE)


def substitute_image_placeholders(question: str) -> str:
    """Replace `[рисунокNNNN]` with `/api/tests/images/рисунокNNNN.png`."""

    def _replace(match: re.Match[str]) -> str:
        filename = f"рисунок{match.group(1)}.png"
        return f"/api/tests/images/{quote(filename)}"

    return _IMAGE_PLACEHOLDER_RE.sub(_replace, question)
