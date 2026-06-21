#!/usr/bin/env python3
"""Export OpenAPI schema from the FastAPI app (Task 95 CI drift check).

Usage (from backend/):
    python scripts/export_openapi.py -o openapi.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

# Schema export must not require a live DB or secrets file.
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "export-openapi-jwt-secret-at-least-32-bytes")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Write FastAPI OpenAPI schema to JSON.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=BACKEND_ROOT / "openapi.json",
        help="Output path (default: backend/openapi.json)",
    )
    args = parser.parse_args()

    app = create_app()
    schema = app.openapi()
    payload = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(f"Wrote OpenAPI schema to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
