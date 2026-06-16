"""Password hashing and JWT access-token utilities.

Sources:
- https://passlib.readthedocs.io/en/stable/lib/passlib.context.html
- https://pyjwt.readthedocs.io/en/stable/usage.html
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """Raised when an access token is missing, malformed, or expired."""


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    *,
    subject: str,
    role: str,
    secret: str,
    algorithm: str,
    expires_minutes: int,
) -> str:
    """Build a signed JWT carrying the user id (sub) and role."""
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str, *, secret: str, algorithm: str) -> dict[str, str]:
    """Decode and validate a JWT; raises TokenError on any failure."""
    try:
        return jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc
