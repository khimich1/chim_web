#!/usr/bin/env bash
# Local dev: backend (FastAPI) + frontend (Next.js).
# Usage (from repo root): ./dev.sh
#
# Backend:  http://localhost:8000  (OpenAPI: /docs)
# Frontend: http://localhost:3000

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/.venv"

TEACHER_EMAIL="${DEV_TEACHER_EMAIL:-teacher@example.com}"
TEACHER_PASSWORD="${DEV_TEACHER_PASSWORD:-teacher-pass}"
FRONTEND_URL="${DEV_FRONTEND_URL:-http://localhost:3000}"
BACKEND_URL="${DEV_BACKEND_URL:-http://localhost:8000}"

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

ensure_env_files() {
  if [[ ! -f "$BACKEND/.env" ]] && [[ -f "$BACKEND/.env.example" ]]; then
    echo "Creating backend/.env from .env.example ..."
    cp "$BACKEND/.env.example" "$BACKEND/.env"
  fi

  if [[ ! -f "$FRONTEND/.env.local" ]]; then
    echo "Creating frontend/.env.local ..."
    printf 'NEXT_PUBLIC_API_URL=%s\n' "$BACKEND_URL" >"$FRONTEND/.env.local"
  fi
}

prepare_backend() {
  (
    cd "$BACKEND"
    # shellcheck disable=SC1091
    source "$VENV/bin/activate"
    echo "Applying migrations..."
    python scripts/repair_dev_db.py
    alembic upgrade head

    echo "Ensuring demo teacher exists ..."
    python -m app.cli.seed_teacher \
      --email "$TEACHER_EMAIL" \
      --password "$TEACHER_PASSWORD" \
      >/dev/null
  )
}

wait_for_url() {
  local url=$1
  local label=$2
  local attempts=${3:-60}

  for ((i = 1; i <= attempts; i++)); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "$label is ready."
      return 0
    fi
    sleep 1
  done

  echo "warning: $label did not respond at $url" >&2
  return 1
}

open_browser() {
  local url=$1

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$url" >/dev/null 2>&1 &
  elif command -v sensible-browser >/dev/null 2>&1; then
    sensible-browser "$url" >/dev/null 2>&1 &
  elif [[ "$(uname -s)" == "Darwin" ]] && command -v open >/dev/null 2>&1; then
    open "$url" >/dev/null 2>&1 &
  else
    echo "Open in browser: $url"
  fi
}

free_port() {
  local port=$1
  local label=$2

  if ! command -v fuser >/dev/null 2>&1; then
    return 0
  fi

  if fuser "${port}/tcp" >/dev/null 2>&1; then
    echo "Port ${port} (${label}) is busy — stopping previous process..."
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
    sleep 1
  fi
}

ensure_process_alive() {
  local pid=$1
  local label=$2

  if [[ -n "${pid}" ]] && ! kill -0 "${pid}" 2>/dev/null; then
    echo "error: ${label} failed to start (check logs above)" >&2
    exit 1
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
ensure_env_files
prepare_backend

free_port 8000 "backend"
free_port 3000 "frontend"

echo "Starting backend on $BACKEND_URL ..."
(
  cd "$BACKEND"
  # shellcheck disable=SC1091
  source "$VENV/bin/activate"
  exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

echo "Starting frontend on $FRONTEND_URL ..."
(
  cd "$FRONTEND"
  # Webpack avoids Turbopack HMR bugs (global-error manifest 500s in Next 16).
  exec npm run dev -- --webpack
) &
FRONTEND_PID=$!

sleep 2
ensure_process_alive "$BACKEND_PID" "Backend"
ensure_process_alive "$FRONTEND_PID" "Frontend"

wait_for_url "$BACKEND_URL/docs" "Backend" 60 || true
wait_for_url "$FRONTEND_URL" "Frontend" 90 || true

open_browser "$FRONTEND_URL"

echo ""
echo "=============================================="
echo "  chim_web — local development"
echo "=============================================="
echo "  Frontend:  $FRONTEND_URL"
echo "  Backend:   $BACKEND_URL/docs"
echo ""
echo "  Teacher login:"
echo "    Email:    $TEACHER_EMAIL"
echo "    Password: $TEACHER_PASSWORD"
echo ""
echo "  Ctrl+C to stop both servers."
echo "=============================================="
echo ""

wait "$BACKEND_PID" "$FRONTEND_PID"
