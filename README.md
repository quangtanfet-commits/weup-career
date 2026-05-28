# WeUp Career

> Nền tảng hướng nghiệp cho học sinh và người đi làm tại Việt Nam.
> _Vươn lên cùng sự nghiệp của bạn — Rise up in your career._

[![CI](https://github.com/org/weup-career/actions/workflows/ci.yml/badge.svg)](https://github.com/org/weup-career/actions)
[![Coverage](https://img.shields.io/badge/coverage-≥95%25-brightgreen)](docs/testing/strategy.md)
[![Security](https://img.shields.io/badge/security-OWASP%20reviewed-blue)](docs/security/threat-model.md)

---

## What it is

**WeUp Career** giúp học sinh, sinh viên và người đi làm tại Việt Nam khám phá bản thân, định hướng và phát triển sự nghiệp.

> ⚠️ **Trạng thái domain:** Bộ tài liệu thiết kế hiện tại được khởi tạo theo domain *Todo* (bản nháp ban đầu). Domain thật đã chốt là **hướng nghiệp**. Tập tính năng sản phẩm đang được định nghĩa lại (Phase 1 — redesign). Phần hạ tầng kỹ thuật bên dưới (stack, CI/CD, quality gates, ADR) tái sử dụng được.

**Định hướng tính năng (đang xác nhận yêu cầu):**

- **Tài khoản đa người dùng** — đăng ký, đăng nhập, quản lý phiên JWT + cookie httpOnly _(reusable)_
- **Hồ sơ hướng nghiệp** — phân theo 2 nhóm: học sinh/sinh viên và người đi làm
- **Trắc nghiệm định hướng** — ví dụ Holland/RIASEC, MBTI _(chờ chốt phạm vi)_
- **Tư vấn chọn ngành / chọn trường** — phù hợp bối cảnh tuyển sinh Việt Nam _(chờ chốt)_
- **Lộ trình kỹ năng & nghề nghiệp** — gợi ý bước phát triển _(chờ chốt)_
- **Kết nối mentor / thông tin thị trường lao động** _(chờ chốt)_

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
git clone https://github.com/org/weup-career.git && cd weup-career
cp .env.example .env          # Edit SECRET_KEY with a random value
docker compose up --build
```

Open **http://localhost** — register an account to get started.

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
weup-career/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── auth/               # Authentication & authorization
│   │   ├── <domain>/           # Feature modules (career domain — TBD redesign)
│   │   └── core/               # Config, DB, logging, middleware
│   ├── migrations/             # Alembic database migrations
│   └── tests/                  # pytest unit + integration tests
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── features/           # Auth + career-domain feature modules (TBD redesign)
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
trivy image weup-career-backend:latest
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

> **Status:** Đã đổi thương hiệu sang **WeUp Career**. Hạ tầng kỹ thuật + ADR tái sử dụng. Domain nghiệp vụ (spec, kiến trúc, TLA+, UX) đang được thiết kế lại từ Todo → Hướng nghiệp.
