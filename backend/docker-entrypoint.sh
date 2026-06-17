#!/bin/sh
set -e

cd /app/backend
alembic upgrade head
exec "$@"
