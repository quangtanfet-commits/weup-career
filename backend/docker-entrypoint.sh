#!/bin/sh
# Run DB migrations to head, then exec the given command (ADR-002/006).
set -e

echo "[entrypoint] running alembic upgrade head"
alembic upgrade head

echo "[entrypoint] seeding assessment instruments (idempotent)"
python -m app.assessments.seed

echo "[entrypoint] seeding competency tree (idempotent)"
python -m app.competency.seed

echo "[entrypoint] seeding career library (idempotent)"
python -m app.careers.seed

echo "[entrypoint] seeding demo school (idempotent)"
python -m app.school.seed

echo "[entrypoint] seeding wellbeing content (idempotent)"
python -m app.wellbeing.seed

echo "[entrypoint] starting: $*"
exec "$@"
