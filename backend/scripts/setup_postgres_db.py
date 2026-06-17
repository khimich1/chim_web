"""Create chim_web PostgreSQL role and database (idempotent)."""
from __future__ import annotations

import asyncio
import sys

import asyncpg

ADMIN_DSN = "postgresql://postgres:postgres@localhost:5432/postgres"
APP_USER = "user"
APP_PASSWORD = "pass"
APP_DB = "chemistry"


async def main() -> int:
    conn = await asyncpg.connect(ADMIN_DSN, timeout=5)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_roles WHERE rolname = $1",
            APP_USER,
        )
        if not exists:
            await conn.execute(
                f'CREATE USER "{APP_USER}" WITH PASSWORD \'{APP_PASSWORD}\''
            )
            print(f"Created role: {APP_USER}")
        else:
            await conn.execute(
                f'ALTER USER "{APP_USER}" WITH PASSWORD \'{APP_PASSWORD}\''
            )
            print(f"Role exists, password reset: {APP_USER}")

        db_exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            APP_DB,
        )
        if not db_exists:
            await conn.execute(f'CREATE DATABASE "{APP_DB}" OWNER "{APP_USER}"')
            print(f"Created database: {APP_DB}")
        else:
            print(f"Database exists: {APP_DB}")

        await conn.execute(
            f'GRANT ALL PRIVILEGES ON DATABASE "{APP_DB}" TO "{APP_USER}"'
        )
    finally:
        await conn.close()

    app_admin = await asyncpg.connect(ADMIN_DSN.replace("/postgres", f"/{APP_DB}"), timeout=5)
    try:
        await app_admin.execute(f'GRANT ALL ON SCHEMA public TO "{APP_USER}"')
        await app_admin.execute(f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{APP_USER}"')
    finally:
        await app_admin.close()

    verify = await asyncpg.connect(
        f"postgresql://{APP_USER}:{APP_PASSWORD}@localhost:5432/{APP_DB}",
        timeout=5,
    )
    try:
        who = await verify.fetchval("SELECT current_user")
        print(f"Verified app connection as: {who}")
    finally:
        await verify.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
