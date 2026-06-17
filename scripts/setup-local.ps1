# One-time local setup: PostgreSQL DB, migrations, demo teacher.
# Requires PostgreSQL running (winget install PostgreSQL.PostgreSQL.16).
# Run from repo root: .\scripts\setup-local.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Backend = Join-Path $Root "backend"

Set-Location $Backend
& .\.venv\Scripts\Activate.ps1

Write-Host "Ensuring PostgreSQL role/database..." -ForegroundColor Cyan
python scripts\setup_postgres_db.py

Write-Host "Applying migrations..." -ForegroundColor Cyan
alembic upgrade head

Write-Host "Seeding teacher (teacher@example.com / teacher-pass)..." -ForegroundColor Cyan
python -m app.cli.seed_teacher --email teacher@example.com --password teacher-pass

Write-Host ""
Write-Host "Done. Restart backend if it is already running:" -ForegroundColor Green
Write-Host "  cd backend"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Write-Host ""
Write-Host "Login: teacher@example.com / teacher-pass"
