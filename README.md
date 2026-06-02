# WeUp Career

> Nền tảng Hướng nghiệp Quốc gia cho học sinh, sinh viên và người đi làm tại Việt Nam.
> _Vươn lên cùng sự nghiệp của bạn — Rise up in your career._

[![CI](https://github.com/org/weup-career/actions/workflows/ci.yml/badge.svg)](https://github.com/org/weup-career/actions)
[![Coverage](https://img.shields.io/badge/coverage-≥95%25-brightgreen)](docs/testing/strategy.md)
[![Security](https://img.shields.io/badge/security-OWASP%20reviewed-blue)](docs/security/threat-model.md)

---

## What it is

**WeUp Career** giúp người học khám phá bản thân, định hướng và phát triển sự nghiệp — hiện thực hóa **5 nội dung hướng nghiệp bắt buộc** theo **TT 16/2026/TT-BGDĐT Điều 5**, dựa trên bộ công cụ chuẩn quốc tế (RIASEC, VIPS, MBTI) và mô hình năng lực hợp nhất từ 3 framework NCDG/ABCD/ECG.

**Tập tính năng (theo `docs/spec.md` — neo vào Điều 5):**

- **Tài khoản đa người dùng + cổng giám hộ <16** — đăng ký, JWT + cookie httpOnly; **đồng ý của người giám hộ là bắt buộc cho trẻ <16** _(Điều 5đ; ADR-010)_
- **Trắc nghiệm định hướng (Điều 5b)** — RIASEC + VIPS + MBTI; kết quả là **dữ liệu nhạy cảm** (mã hóa + audit; ADR-011)
- **Thư viện ngành/nghề (Điều 5a)** — thông tin nghề, trường, GDNN, xu hướng thị trường
- **Kỹ năng lựa chọn nghề (Điều 5c)** — lộ trình ra quyết định, so sánh ngành
- **Trải nghiệm nghề (Điều 5d)** — mô phỏng "một ngày làm nghề"
- **Gợi ý nghề/lộ trình có giải thích** — AI human-in-the-loop, **không ép buộc phân luồng** _(ADR-012)_
- **Đo tiến bộ năng lực 2 trục** — K-A-R × giai đoạn phát triển; cây 12 năng lực _(ADR-013)_
- **Module sức khỏe tinh thần** (ABCD NL4, gắn TT 18/2025) + **kênh tư vấn học đường 3 tầng** (B2B2C trường học)

**Phạm vi MVP:** Học sinh THCS + THPT → mở rộng Tiểu học → người đi làm.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 |
| Database | SQLite 3.45 (MVP) → PostgreSQL (production); trường nhạy cảm mã hóa (Field Crypto) |
| Auth | JWT (HS256) + httpOnly refresh cookies, bcrypt; Consent Guard + RBAC quan hệ |
| Frontend | Next.js 16 (App Router), React 19, TypeScript 5 (strict) — xem [ADR-014](docs/adr/ADR-014-frontend-framework.md) |
| State | TanStack Query v5 (server) + Zustand (client) |
| UI | Tailwind CSS, shadcn/ui (Radix), Framer Motion, Recharts (biểu đồ tiến bộ) |
| Proxy | Nginx (TLS, rate limiting, reverse-proxy tới Next.js runtime) |
| CI/CD | GitHub Actions (gồm bias test + TLC) |
| Containers | Docker, Docker Compose |

---

## Quick Start

**Requirements:** Docker + Docker Compose

```bash
git clone https://github.com/org/weup-career.git && cd weup-career
cp .env.example .env          # Đặt SECRET_KEY và FIELD_ENCRYPTION_KEY (openssl rand -hex 32)
docker compose up --build
```

Mở **http://localhost** — đăng ký tài khoản để bắt đầu (người <16 sẽ qua luồng đồng ý giám hộ).

API documentation: **http://localhost/api/v1/docs**

---

## Documentation

Theo [Diátaxis](https://diataxis.fr/) + [arc42](https://arc42.org/).

### Nền tảng domain (đọc trước)
- [Master NLSpec](docs/spec.md) — đặc tả sản phẩm (8 phần, 8 thuộc tính đúng đắn)
- [Căn cứ pháp lý](docs/legal/legal-basis.md) — VBPL VN, TT 16/2026 Điều 5, BVDLCN, AI governance
- [Tổng hợp 3 framework quốc tế](docs/research/career-frameworks-synthesis.md) — mô hình 2 trục, crosswalk Điều 5
- [Thư viện nguồn](docs/research/sources.md)

### Reference
- [API Contract](http://localhost/api/v1/docs) — OpenAPI 3.1 (live)
- [Architecture Overview](docs/architecture/overview.md) — C4 + component
- [Data Flow](docs/architecture/data-flow.md) · [Security Design](docs/security/auth-design.md)

### Explanation
- [Architecture Decisions](docs/adr/) — 13 ADR
- [Threat Model](docs/security/threat-model.md) — STRIDE + AI threats
- [Formal Verification](docs/formal-verification/tla-spec-design.md) — TLA+ (CP-1…CP-8)
- [Scalability](docs/scalability/strategy.md) · [Testing](docs/testing/strategy.md)

---

## Project Structure

```
weup-career/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── auth/               # Xác thực, token
│   │   ├── guardians/          # GuardianLink, GuardianConsent (<16)
│   │   ├── assessments/        # RIASEC/VIPS/MBTI (dữ liệu nhạy cảm)
│   │   ├── competency/         # Cây 12 năng lực, tiến bộ K-A-R
│   │   ├── careers/            # Thư viện nghề, nội dung, lộ trình
│   │   ├── reco/               # Gợi ý (human-in-the-loop)
│   │   ├── counseling/         # Trường, lớp, phiên tư vấn 3 tầng
│   │   └── core/               # config, db, consent, authz, audit, crypto, logging
│   ├── migrations/             # Alembic
│   └── tests/                  # pytest unit + integration
├── frontend/                   # Next.js 16 App Router (features: auth, guardian, assessment,
│   │                           #   competency, careers, reco, wellbeing, counseling)
│   └── e2e/                    # Playwright
├── nginx/                      # Nginx config
├── tla/                        # TLA+ specs (ConsentLifecycle, SensitiveDataAccess, …)
├── docs/                       # spec.md, legal/, research/, architecture/, adr/,
│                               #   security/, testing/, ux/, formal-verification/,
│                               #   scalability/, operations/
├── scenarios/                  # Holdout scenarios (coder không xem)
├── docker-compose.yml · docker-compose.prod.yml · .env.example
```

---

## Development

```bash
docker compose exec backend pytest --cov=app --cov-report=term-missing
docker compose exec frontend npm test
docker compose exec frontend npx playwright test
docker compose exec backend mypy app/ --strict
trivy image weup-career-backend:latest
```

---

## Quality Gates (CI)

| Gate | Tool | Threshold |
|------|------|-----------|
| Python types | mypy --strict | Zero errors |
| Backend tests | pytest | ≥95% (100% consent/sensitive/auth/reco) |
| Frontend tests | vitest | ≥95% |
| TypeScript | tsc --noEmit | Zero errors |
| Linting | ruff + eslint | Zero warnings |
| Container scan | Trivy | No HIGH/CRITICAL |
| SAST | Semgrep | Zero findings |
| **Bias test** | công bằng giới/vùng/hoàn cảnh | Trong ngưỡng (NFR-12) |
| E2E | Playwright (3 browsers) | All pass |
| TLA+ | TLC | CP-1…CP-8 pass |

---

## Architecture Decision Records

| ADR | Decision |
|-----|---------|
| [ADR-001](docs/adr/ADR-001-framework-selection.md) | FastAPI (backend) — frontend SPA **superseded bởi ADR-014** |
| [ADR-002](docs/adr/ADR-002-database.md) | SQLite → PostgreSQL qua SQLAlchemy abstraction |
| [ADR-003](docs/adr/ADR-003-api-style.md) | REST over HTTP/JSON, OpenAPI 3.1 |
| [ADR-004](docs/adr/ADR-004-state-management.md) | TanStack Query + Zustand |
| [ADR-005](docs/adr/ADR-005-testing-strategy.md) | pytest + Vitest + Playwright + bias test |
| [ADR-006](docs/adr/ADR-006-docker-strategy.md) | Multi-stage builds, dev/prod compose |
| [ADR-007](docs/adr/ADR-007-cicd.md) | GitHub Actions, parallel gates |
| [ADR-008](docs/adr/ADR-008-security-controls.md) | JWT + httpOnly, OWASP Top 10 |
| [ADR-009](docs/adr/ADR-009-scalability.md) | Stateless, hexagonal, scale-up path |
| [ADR-010](docs/adr/ADR-010-guardian-consent.md) | **Kiến trúc đồng ý giám hộ <16 (CP-1/CP-2)** |
| [ADR-011](docs/adr/ADR-011-sensitive-data.md) | **Mã hóa + audit dữ liệu nhạy cảm (CP-3)** |
| [ADR-012](docs/adr/ADR-012-ai-recommendation-governance.md) | **AI governance: human-in-the-loop, bias (CP-5/6)** |
| [ADR-013](docs/adr/ADR-013-two-axis-competency-model.md) | **Mô hình năng lực 2 trục K-A-R × giai đoạn** |
| [ADR-014](docs/adr/ADR-014-frontend-framework.md) | **Next.js 16 App Router + React 19 (thay React 18 + Vite SPA)** |

---

## Contributing

1. Branch từ `main` → `feat/<topic>` hoặc `fix/<topic>`
2. Viết test trước (TDD)
3. Mọi CI gate phải pass trước khi mở PR
4. Squash merge sau khi được duyệt

---

## License

MIT — xem [LICENSE](LICENSE)
