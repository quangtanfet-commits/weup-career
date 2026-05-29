#!/bin/sh
# Run DB migrations to head, then exec the given command (ADR-002/006).
set -e

echo "[entrypoint] running alembic upgrade head"
alembic upgrade head

echo "[entrypoint] starting: $*"
exec "$@"
