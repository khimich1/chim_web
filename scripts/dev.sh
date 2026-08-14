#!/usr/bin/env bash
# Wrapper for repo-root dev.sh (migrations, seed teacher, both servers).
# Usage (from repo root): ./scripts/dev.sh
#
# Prefer ./dev.sh — this path exists for older docs and habits.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -x "$ROOT/dev.sh" ]]; then
  echo "error: dev launcher not found at $ROOT/dev.sh" >&2
  exit 1
fi

exec "$ROOT/dev.sh" "$@"
