"""HTTP rate limiting via slowapi (in-memory, single-node).

Login and tutor chat are the highest-risk endpoints for brute force and LLM cost.
Limits are configurable through Settings for tests and deployment tuning.

Route decorators from slowapi break FastAPI body/Depends binding when the module
uses ``from __future__ import annotations``; enforcement runs in FastAPI Depends
instead (see security-and-hardening.mdc).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from limits.util import parse_many
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.wrappers import Limit

from app.api.deps import get_app_settings
from app.core.config import Settings

limiter = Limiter(key_func=get_remote_address)


def reset_limiter_storage() -> None:
    """Clear in-memory counters — use in pytest to avoid cross-test bleed."""
    limiter.reset()


def _enforce_rate_limit(request: Request, limit_value: str) -> None:
    limits = parse_many(limit_value)
    key = get_remote_address(request)
    for item in limits:
        if not limiter.limiter.hit(item, key):
            raise RateLimitExceeded(
                Limit(
                    item,
                    get_remote_address,
                    None,
                    False,
                    None,
                    None,
                    None,
                    1,
                    False,
                )
            )


def enforce_login_rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> None:
    _enforce_rate_limit(request, settings.auth_login_rate_limit)


def enforce_tutor_message_rate_limit(
    request: Request,
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> None:
    _enforce_rate_limit(request, settings.tutor_message_rate_limit)
