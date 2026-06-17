"""Create the first teacher account (MVP: single teacher per instance)."""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.security import hash_password, verify_password
from app.models import User, UserRole


async def seed_teacher(
    email: str,
    password: str,
    *,
    reset_password: bool = False,
) -> User:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            existing = await session.scalar(select(User).where(User.email == email))
            if existing is not None:
                if existing.role != UserRole.TEACHER:
                    raise ValueError(f"User {email} exists but is not a teacher")
                if reset_password:
                    existing.password_hash = hash_password(password)
                    existing.is_active = True
                    await session.commit()
                    await session.refresh(existing)
                    print(f"Reset password for teacher: {email}")
                    return existing
                print(f"Teacher already exists: {email}")
                return existing

            teacher = User(
                email=email,
                password_hash=hash_password(password),
                role=UserRole.TEACHER,
                is_active=True,
            )
            session.add(teacher)
            await session.commit()
            await session.refresh(teacher)
            print(f"Created teacher: {email} (id={teacher.id})")
            return teacher
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seed the initial teacher account")
    parser.add_argument("--email", required=True, help="Teacher email")
    parser.add_argument("--password", required=True, help="Initial password")
    parser.add_argument(
        "--reset-password",
        action="store_true",
        help="Update password_hash for an existing teacher account",
    )
    args = parser.parse_args(argv)

    try:
        teacher = asyncio.run(
            seed_teacher(
                args.email,
                args.password,
                reset_password=args.reset_password,
            )
        )
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not verify_password(args.password, teacher.password_hash):
        print("Error: password hash verification failed", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
