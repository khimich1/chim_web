"""Replace image placeholders in test question text with API image URLs."""

from __future__ import annotations

import re
from urllib.parse import quote

# Matches [рисунок0001], [рисунок0002], …
_IMAGE_PLACEHOLDER_RE = re.compile(r"\[рисунок(\d+)\]", re.IGNORECASE)
# Matches [ответ0001], [ответ0002], … (written-task reference images, SPEC §1.10)
_ANSWER_PLACEHOLDER_RE = re.compile(r"\[ответ(\d+)\]", re.IGNORECASE)


def substitute_image_placeholders(question: str) -> str:
    """Replace `[рисунокNNNN]` with `/api/tests/images/рисунокNNNN.png`."""

    def _replace(match: re.Match[str]) -> str:
        filename = f"рисунок{match.group(1)}.png"
        return f"/api/tests/images/{quote(filename)}"

    return _IMAGE_PLACEHOLDER_RE.sub(_replace, question)


def reference_answer_blocks_from_correct_ans(correct_ans: str) -> list[dict]:
    """Build ContentBlock-like dicts from exam `correct_ans` (SPEC §1.10)."""
    text = correct_ans.strip()
    if not text:
        return []

    blocks: list[dict] = []
    pos = 0
    for match in _ANSWER_PLACEHOLDER_RE.finditer(correct_ans):
        before = correct_ans[pos : match.start()]
        if before.strip():
            blocks.append({"type": "text", "content": before})
        filename = f"ответ{match.group(1)}.png"
        blocks.append(
            {
                "type": "image",
                "url": f"/api/tests/images/{quote(filename)}",
            }
        )
        pos = match.end()
    tail = correct_ans[pos:]
    if tail.strip():
        blocks.append({"type": "text", "content": tail})
    if not blocks:
        blocks.append({"type": "text", "content": text})
    return blocks
