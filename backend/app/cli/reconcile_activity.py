"""Reconcile missing HOMEWORK_COMPLETE / STEP_CORRECT ledger rows.

Dry-run by default; write only with ``--apply``. Optional ``--student-id``.

    python -m app.cli.reconcile_activity
    python -m app.cli.reconcile_activity --student-id <uuid>
    python -m app.cli.reconcile_activity --apply
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models import User, UserRole
from app.services.activity_service import ActivityService


class StudentNotFoundError(ValueError):
    """CLI: --student-id does not match an active student."""


async def reconcile_activity(
    *,
    apply: bool,
    student_id: uuid.UUID | None = None,
) -> list[tuple[uuid.UUID, int]]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            if student_id is not None:
                user = await session.get(User, student_id)
                if user is None or user.role != UserRole.STUDENT:
                    raise StudentNotFoundError(
                        f"Unknown student id: {student_id}"
                    )
                targets = [user.id]
            else:
                targets = list(
                    (
                        await session.scalars(
                            select(User.id).where(
                                User.role == UserRole.STUDENT,
                                User.is_active.is_(True),
                            )
                        )
                    ).all()
                )

            activity = ActivityService(session)
            rows: list[tuple[uuid.UUID, int]] = []
            for target_id in targets:
                created = await activity.reconcile_student(target_id)
                rows.append((target_id, created))
            if apply:
                await session.commit()
            else:
                await session.rollback()
            return rows
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile missing HOMEWORK_COMPLETE and STEP_CORRECT events. "
            "Dry-run unless --apply is set."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing events (default is dry-run)",
    )
    parser.add_argument(
        "--student-id",
        default=None,
        help="Limit to one student UUID",
    )
    args = parser.parse_args(argv)

    parsed_student_id: uuid.UUID | None = None
    if args.student_id is not None:
        try:
            parsed_student_id = uuid.UUID(args.student_id)
        except ValueError:
            print(f"Error: invalid student id: {args.student_id}", file=sys.stderr)
            return 1

    try:
        rows = asyncio.run(
            reconcile_activity(apply=args.apply, student_id=parsed_student_id)
        )
    except StudentNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    total = 0
    for student_uuid, created in rows:
        print(f"{student_uuid} {created}")
        total += created
    mode = "apply" if args.apply else "dry-run"
    print(f"created={total} mode={mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
