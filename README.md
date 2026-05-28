# ✓ Todos

> A production-grade Todo application. Simple interface. Solid engineering underneath.

[![CI](https://github.com/org/todo-app/actions/workflows/ci.yml/badge.svg)](https://github.com/org/todo-app/actions)
[![Coverage](https://img.shields.io/badge/coverage-≥95%25-brightgreen)](docs/testing/strategy.md)
[![Security](https://img.shields.io/badge/security-OWASP%20reviewed-blue)](docs/security/threat-model.md)

---

## What it is

A full-stack Todo application with:

- **Multi-user auth** — register, login, JWT + httpOnly cookie session management
- **Rich todo management** — title, description, priority, due date, status tracking
- **Tagging** — create tags, assign to todos, filter by tag
- **Drag-and-drop reorder** — manual ordering persisted server-side
- **Optimistic updates** — every action responds instantly; network syncs in background
- **Soft delete + undo** — delete with a 5-second undo window
- **Keyboard-first UX** — power users never need to reach for the mouse

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | SQLite 3.45 (WAL mode), aiosqlite |
| Auth | JWT (HS256) + httpOnly refresh cookies, bcrypt |
| Frontend | React 18, TypeScript 5, Vite 5 |
| State | TanStack Query v5 (server) + Zustand (client) |
| UI | Tailwind CSS, Radix UI, Framer Motion, @dnd-kit |
| Proxy | Nginx (TLS, rate limiting, static serving) |
| CI/CD | GitHub Actions |
| Containers | Docker, Docker Compose |

---

## Quick Start

**Requirements:** Docker + Docker Compose

```bash
git clone https://github.com/org/todo-app.git && cd todo-app
cp .env.example .env          # Edit SECRET_KEY with a random value
docker compose up --build
```

Open **http://localhost** — register an account — start adding todos.

API documentation: **http://localhost/api/v1/docs**

---

## Documentation

This project follows the [Diátaxis](https://diataxis.fr/) documentation framework and [arc42](https://arc42.org/) architecture structure.

### Tutorials (Learning-oriented)
- [Quick Start](README.md#quick-start) — Get running in 2 minutes
- [Local Development Guide](docs/operations/deployment-guide.md) — Dev environment setup

### How-To Guides (Task-oriented)
- [Deployment Guide](docs/operations/deployment-guide.md) — Production deployment
- [Database Migrations](docs/operations/deployment-guide.md#database-migrations) — Schema changes
- [Rotating Secrets](docs/operations/runbook.md#runbook-4-rotating-jwt-secret-key) — Key rotation

### Reference (Information-oriented)
- [API Contract](http://localhost/api/v1/docs) — OpenAPI 3.1 (live docs)
- [Architecture Overview](docs/architecture/overview.md) — C4 model + component diagrams
- [Data Flow](docs/architecture/data-flow.md) — Request/response flows
- [Security Design](docs/security/auth-design.md) — Auth & authorization model

### Explanation (Understanding-oriented)
- [Architecture Decisions](docs/adr/) — Why we chose each technology
- [Threat Model](docs/security/threat-model.md) — STRIDE analysis
- [Formal Verification](docs/formal-verification/tla-spec-design.md) — TLA+ specification design
- [Scalability Strategy](docs/scalability/strategy.md) — Growth path
- [Testing Strategy](docs/testing/strategy.md) — Test architecture

---

## Project Structure

```
todo-app/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── auth/               # Authentication & authorization
│   │   ├── todos/              # Todo CRUD + reorder
│   │   ├── tags/               # Tag management
│   │   └── core/               # Config, DB, logging, middleware
│   ├── migrations/             # Alembic database migrations
│   └── tests/                  # pytest unit + integration tests
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── features/           # Auth, todos, tags feature modules
│   │   ├── components/         # Shared UI components
│   │   ├── api/                # Typed API client
│   │   └── store/              # Zustand state stores
│   └── e2e/                    # Playwright E2E tests
├── nginx/                      # Nginx configuration
├── tla/                        # TLA+ formal specifications
├── docs/                       # All documentation
│   ├── spec.md                 # Master NLSpec
│   ├── architecture/           # Diagrams and architecture docs
│   ├── adr/                    # Architecture Decision Records
│   ├── security/               # Threat model, auth design
│   ├── testing/                # Test strategy
│   ├── ux/                     # User flows, wireframes
│   ├── formal-verification/    # TLA+ spec design
│   ├── scalability/            # Growth strategy
│   └── operations/             # Runbook, deployment guide
├── scenarios/                  # Holdout test scenarios (not seen by coder)
├── docker-compose.yml          # Development
├── docker-compose.prod.yml     # Production overrides
└── .env.example                # Environment template
```

---

## Development

```bash
# Backend tests
docker compose exec backend pytest --cov=app --cov-report=term-missing

# Frontend tests
docker compose exec frontend npm test

# E2E tests (requires running stack)
docker compose exec frontend npx playwright test

# Type checking
docker compose exec backend mypy app/ --strict
docker compose exec frontend npx tsc --noEmit

# Security scan
docker compose exec backend pip-audit
trivy image todo-backend:latest
```

---

## Quality Gates (CI)

Every PR must pass:

| Gate | Tool | Threshold |
|------|------|-----------|
| Python types | mypy --strict | Zero errors |
| Backend tests | pytest | ≥95% coverage |
| Frontend tests | vitest | ≥95% coverage |
| TypeScript | tsc --noEmit | Zero errors |
| Linting | ruff + eslint | Zero warnings |
| Container scan | Trivy | No HIGH/CRITICAL CVEs |
| SAST | Semgrep | Zero findings |
| E2E | Playwright (3 browsers) | All pass |
| TLA+ | TLC model checker | No invariant violations |

---

## Architecture Decision Records

| ADR | Decision |
|-----|---------|
| [ADR-001](docs/adr/ADR-001-framework-selection.md) | FastAPI + React + TypeScript + Vite |
| [ADR-002](docs/adr/ADR-002-database.md) | SQLite with SQLAlchemy abstraction for future migration |
| [ADR-003](docs/adr/ADR-003-api-style.md) | REST over HTTP/JSON, OpenAPI 3.1 |
| [ADR-004](docs/adr/ADR-004-state-management.md) | TanStack Query + Zustand (two-state model) |
| [ADR-005](docs/adr/ADR-005-testing-strategy.md) | pytest + Vitest + Playwright multi-browser |
| [ADR-006](docs/adr/ADR-006-docker-strategy.md) | Multi-stage builds, dev/prod compose split |
| [ADR-007](docs/adr/ADR-007-cicd.md) | GitHub Actions, parallel gates, manual prod approval |
| [ADR-008](docs/adr/ADR-008-security-controls.md) | JWT + httpOnly cookies, OWASP Top 10 mitigations |
| [ADR-009](docs/adr/ADR-009-scalability.md) | Stateless backend, hexagonal architecture, scale-up path |

---

## Contributing

1. Branch from `main` → `feat/<topic>` or `fix/<topic>`
2. Write tests first (TDD)
3. All CI gates must pass before opening PR
4. Squash merge after approval

---

## License

MIT — see [LICENSE](LICENSE)

---

> **Status:** Phase 1 (Planning) complete. Awaiting implementation approval.
