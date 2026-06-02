# WeUp Career — Backend

FastAPI backend for the WeUp Career platform. This package contains **slice 1**:
the legal core — authentication and guardian consent.

## Stack
Python 3.12 · FastAPI · SQLAlchemy 2.0 (async) · Pydantic v2 · Alembic ·
SQLite (aiosqlite, abstracted for PostgreSQL) · structlog · uv.

Architecture: hexagonal (ports & adapters) — services contain pure logic and
never import FastAPI; repositories are Protocol ports with SQLAlchemy adapters.

## Quick start (local)
```bash
uv sync                       # install deps
cp .env.example .env          # fill SECRET_KEY + FIELD_ENCRYPTION_KEY
uv run alembic upgrade head   # create schema
uv run uvicorn app.main:get_app --factory --reload
```
Open http://localhost:8000/api/v1/docs

## Docker
```bash
docker compose up             # from repo root
```
Health: `GET /api/v1/health` · Readiness: `GET /api/v1/ready`

## Tests & quality gates
```bash
uv run pytest --cov=app --cov-report=term-missing
uv run mypy app
uv run ruff check app tests
```

## Slice-1 scope
- `app/core/` — config, database, security (JWT+bcrypt), consent guard (CP-1/CP-2),
  authz (CP-4), audit (CP-3 ready), field crypto (ADR-011), logging, middleware.
- `app/auth/` — User, RefreshToken; register/login/refresh/logout/me; atomic
  refresh rotation (CP-7).
- `app/guardians/` — GuardianLink, GuardianConsent; invite/consent/revoke;
  self-consent forbidden.

Out of scope (later slices): assessments, competency, careers, reco, counseling.
