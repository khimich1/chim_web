#!/usr/bin/env python3
"""CLI: migrate EGE written tasks (29–34) into test_ege.db (Task 86)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ege_written_migration import (  # noqa: E402
    apply_migration_plan,
    build_migration_plan,
    default_target_db,
    export_skipped_rows,
    format_report,
    resolve_source_db,
)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate EGE written tasks (types 29–34) into test_ege.db",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Path to ege (копия).db (default: auto-detect ege*.db in repo root)",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=None,
        help="Path to test_ege.db (default: repo root / test_ege.db)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and print migration plan without writing",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Apply migration to target database",
    )
    parser.add_argument(
        "--export-skipped",
        type=Path,
        default=None,
        help="Export skipped NULL-variant rows to JSON or CSV (by extension)",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source = args.source or resolve_source_db()
    target = args.target or default_target_db()

    if not source.is_file():
        print(f"Source database not found: {source}", file=sys.stderr)
        return 1
    if not target.is_file():
        print(f"Target database not found: {target}", file=sys.stderr)
        return 1

    plan = build_migration_plan(source, target)
    print(format_report(plan))

    if args.export_skipped:
        fmt = "csv" if args.export_skipped.suffix.lower() == ".csv" else "json"
        export_skipped_rows(plan.skipped_null_variant, args.export_skipped, fmt=fmt)
        print(f"Exported {len(plan.skipped_null_variant)} skipped rows to {args.export_skipped}")

    if args.dry_run:
        return 0

    apply_migration_plan(target, plan)
    print(f"Applied {len(plan.records)} records to {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
