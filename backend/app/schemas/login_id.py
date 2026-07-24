"""Shared login identifier rules (stored in users.email; API key remains email)."""

from __future__ import annotations

import re

# After strip().lower(); ASCII latin + digits + . _ @ + -
LOGIN_RE = re.compile(r"^[a-z0-9._@+-]{3,64}$")
LOGIN_MAX_LENGTH = 64
LOGIN_MIN_LENGTH = 3
LOGIN_FORMAT_ERROR = (
    "Login must be 3–64 chars: latin letters, digits, . _ @ + -"
)


def normalize_login(value: str) -> str:
    """Strip, lower-case, and validate login identifier format."""
    login = value.strip().lower()
    if not LOGIN_RE.fullmatch(login):
        raise ValueError(LOGIN_FORMAT_ERROR)
    return login
