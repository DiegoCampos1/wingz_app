#!/usr/bin/env bash
set -e

# Wait for PostgreSQL to accept connections before running migrations.
echo "Waiting for PostgreSQL at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
until pg_isready -h "${POSTGRES_HOST:-db}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-wingz}" >/dev/null 2>&1; do
  sleep 1
done
echo "PostgreSQL is ready."

# Apply database migrations.
python manage.py migrate --noinput

# Optionally load demo data (dev only). Idempotent: a no-op if rides already exist.
if [ "${DJANGO_SEED_DEMO:-0}" = "1" ]; then
  python manage.py seed_demo
fi

# Hand off to the container command (dev server, gunicorn, etc.).
exec "$@"
