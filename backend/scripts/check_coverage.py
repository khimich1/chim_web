#!/usr/bin/env python3
"""Task 29 coverage gate - >=80% per MVP domain (SPEC section 5, tasks/plan.md).

Domains: auth, homework, test_sessions, notifications (routers + services).

Usage (from backend/):
    python scripts/check_coverage.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
THRESHOLD = 80

# Paths relative to backend/app/
DOMAINS: dict[str, list[str]] = {
    "auth": [
        "api/routers/auth.py",
        "services/auth_service.py",
    ],
    "homework": [
        "api/routers/homework.py",
        "api/routers/student_homework.py",
        "services/homework_service.py",
        "services/homework_submit_service.py",
    ],
    "test_sessions": [
        "api/routers/test_sessions.py",
        "services/test_session_service.py",
    ],
    "notifications": [
        "api/routers/notifications.py",
        "services/notification_service.py",
    ],
}

COV_MODULES = [
    f"app.{path.replace('/', '.').removesuffix('.py')}"
    for files in DOMAINS.values()
    for path in files
]


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").lower()


def _domain_coverage(report: dict, rel_paths: list[str]) -> tuple[float, int, int, list[str]]:
    files = report.get("files", {})
    suffixes = {p.lower() for p in rel_paths}
    total_stmts = 0
    covered_stmts = 0
    lines: list[str] = []

    for file_path, info in files.items():
        normalized = _normalize_path(file_path)
        if not any(normalized.endswith(suffix) for suffix in suffixes):
            continue
        summary = info["summary"]
        stmts = summary["num_statements"]
        missing = summary["missing_lines"]
        covered = stmts - missing
        total_stmts += stmts
        covered_stmts += covered
        pct = 100.0 * covered / stmts if stmts else 100.0
        lines.append(f"    {file_path}: {pct:.0f}% ({covered}/{stmts})")

    pct_total = 100.0 * covered_stmts / total_stmts if total_stmts else 0.0
    return pct_total, covered_stmts, total_stmts, lines


def main() -> int:
    coverage_json = BACKEND_ROOT / "coverage.json"
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *[f"--cov={module}" for module in COV_MODULES],
        f"--cov-report=json:{coverage_json.name}",
        "--cov-report=term-missing:skip-covered",
        "-q",
    ]

    print("Running pytest with coverage gate modules...")
    result = subprocess.run(cmd, cwd=BACKEND_ROOT, check=False)
    if result.returncode != 0:
        print("pytest failed - fix tests before checking coverage thresholds.")
        return result.returncode

    if not coverage_json.exists():
        print("coverage.json not found after pytest run.")
        return 1

    report = json.loads(coverage_json.read_text(encoding="utf-8"))
    failed: list[str] = []

    print(f"\nCoverage gate (threshold >={THRESHOLD}% per domain):\n")
    for domain, paths in DOMAINS.items():
        pct, covered, total, file_lines = _domain_coverage(report, paths)
        status = "PASS" if pct >= THRESHOLD else "FAIL"
        print(f"  [{status}] {domain}: {pct:.1f}% ({covered}/{total})")
        for line in file_lines:
            print(line)
        if pct < THRESHOLD:
            failed.append(f"{domain} ({pct:.1f}%)")
        print()

    if failed:
        print(f"Coverage gate FAILED - below {THRESHOLD}%: {', '.join(failed)}")
        return 1

    print(f"Coverage gate PASSED - all domains >={THRESHOLD}%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
