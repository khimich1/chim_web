# Start PostgreSQL for local dev (matches backend/.env.example DATABASE_URL).
# Requires Docker Desktop: https://www.docker.com/products/docker-desktop/

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Install Docker Desktop, then run this script again." -ForegroundColor Red
    Write-Host "Or install PostgreSQL 16+ manually and create DB 'chemistry' with user/pass from backend/.env"
    exit 1
}

Set-Location $Root
docker compose up -d postgres

Write-Host "Waiting for PostgreSQL..." -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    $status = docker inspect --format='{{.State.Health.Status}}' chim-postgres 2>$null
    if ($status -eq "healthy") {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $ready) {
    Write-Host "PostgreSQL container did not become healthy in time. Check: docker compose logs postgres" -ForegroundColor Yellow
    exit 1
}

Write-Host "PostgreSQL is ready on localhost:5432 (user/pass/db: user/pass/chemistry)" -ForegroundColor Green
