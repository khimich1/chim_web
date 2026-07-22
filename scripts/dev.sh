#!/usr/bin/env bash
# Start backend (FastAPI) + frontend (Next.js) for local development.
# Usage (from repo root): ./scripts/dev.sh
#
# Backend: http://localhost:8000  (OpenAPI: /docs)
# Frontend: http://localhost:3000

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  echo ""
  echo "Stopping..."
  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [[ -n "${BACKEND_PID}" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  echo "Stopped."
}
trap cleanup EXIT INT TERM

ensure_venv() {
  if [[ ! -d "$VENV" ]]; then
    echo "Creating backend venv at $VENV ..."
    python3 -m venv "$VENV"
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
    pip install -r "$BACKEND/requirements.txt"
  else
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
  fi
}

if [[ ! -f "$BACKEND/app/main.py" ]]; then
  echo "error: backend not found at $BACKEND" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND" ]] || [[ ! -f "$FRONTEND/package.json" ]]; then
  echo "error: frontend not found at $FRONTEND" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  (cd "$FRONTEND" && npm install)
fi

ensure_venv

echo "Starting backend on http://localhost:8000 ..."
(
  cd "$BACKEND"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend on http://localhost:3000 ..."
(
  cd "$FRONTEND"
  exec npm run dev
) &
FRONTEND_PID=$!

echo ""
echo "  Backend:  http://localhost:8000/docs"
echo "  Frontend: http://localhost:3000"
echo "  Ctrl+C to stop both."
echo ""

wait "$BACKEND_PID" "$FRONTEND_PID"
