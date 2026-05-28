# NLSpec: Production-Grade Todo Application

**Version:** 1.0.0  
**Date:** 2026-05-27  
**Status:** DRAFT — Awaiting Implementation Approval  
**Author:** Engineering Team

---

## 1. PURPOSE

Build a **production-grade Todo application** with a clean separation of concerns between a RESTful backend API and a single-page application (SPA) frontend. The system must be deployable via Docker Compose in a single command, support multi-user authentication, and be designed from the outset to scale horizontally when SQLite is replaced by a networked database.

**Goals:**
- Demonstrate enterprise software engineering practices at small scale
- Provide a clean reference implementation for backend + frontend + auth + testing + CI/CD
- Run fully locally with zero external service dependencies
- Be extensible without architectural rewrites

**Non-Goals:**
- Real-time collaboration (WebSockets) — deferred to v2
- Mobile native apps — web-responsive only
- Multi-tenancy with isolated schemas — single shared schema with row-level ownership
- Third-party OAuth/OIDC in v1 — username/password only with JWT

---

## 2. ACTORS

| Actor | Description |
|-------|-------------|
| **Anonymous User** | Can view the login/register page; no access to todo data |
| **Authenticated User** | Can manage their own todos (create, read, update, delete, reorder) |
| **System (Backend)** | Processes requests, enforces authorization, persists data, emits structured logs |
| **CI Pipeline** | Runs quality gates, security scans, coverage checks, publishes artifacts |
| **Operator** | Deploys, monitors, rotates secrets, manages backups |

---

## 3. FUNCTIONAL REQUIREMENTS

### 3.1 Authentication & Identity
- FR-01: User can register with email + password (email uniqueness enforced)
- FR-02: User can log in and receive a short-lived access token (15 min) + httpOnly refresh token (7 days)
- FR-03: Access token can be silently refreshed before expiry using the refresh token
- FR-04: User can log out; refresh token is revoked server-side
- FR-05: Passwords are validated for minimum complexity (≥8 chars, mixed case, digit)
- FR-06: Email is normalized (lowercase, trimmed) before storage

### 3.2 Todo Management
- FR-10: User can create a todo with a title (required), optional description, optional due date, optional priority (low/medium/high)
- FR-11: User can list all their todos with optional filters: status (open/in-progress/done), priority, search text, due date range
- FR-12: User can view a single todo by ID
- FR-13: User can update any field of their own todo
- FR-14: User can delete their own todo (soft delete, 30-day recovery window)
- FR-15: User can restore a soft-deleted todo within the recovery window
- FR-16: User can permanently delete a todo (irreversible)
- FR-17: Todo items have a manual sort order that persists across sessions
- FR-18: User can reorder todos via a bulk reorder endpoint (drag-and-drop support)
- FR-19: User can mark a todo complete or incomplete (shortcut for status transition)

### 3.3 Tagging
- FR-20: User can create, rename, and delete tags
- FR-21: User can assign/remove tags from a todo (many-to-many)
- FR-22: User can filter todos by one or more tags

### 3.4 Profile & Account
- FR-30: User can view their profile (email, joined date, todo counts)
- FR-31: User can change their password (requires current password)
- FR-32: User can request account deletion (soft delete with 30-day window)

---

## 4. NON-FUNCTIONAL REQUIREMENTS

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Performance | p99 API latency < 100ms for all read operations under 50 concurrent users |
| NFR-02 | Performance | p99 API latency < 200ms for all write operations |
| NFR-03 | Availability | Target 99.9% uptime in production deployment |
| NFR-04 | Security | All endpoints authenticated; no authorization bypass possible |
| NFR-05 | Security | Passwords stored as bcrypt hash (cost ≥12) |
| NFR-06 | Security | No PII in logs; tokens never logged |
| NFR-07 | Security | Rate limiting: 20 auth req/min per IP, 200 API req/min per user |
| NFR-08 | Observability | Structured JSON logs with correlation IDs on every request |
| NFR-09 | Observability | Health + readiness endpoints for container orchestration |
| NFR-10 | Reliability | Graceful shutdown; in-flight requests complete before process exit |
| NFR-11 | Testability | ≥95% meaningful line coverage; 100% coverage on auth and data-access layers |
| NFR-12 | Maintainability | All public API contracts documented via OpenAPI 3.1 |
| NFR-13 | Accessibility | Frontend meets WCAG 2.1 AA |
| NFR-14 | Responsiveness | UI works correctly on viewports 320px–2560px |
| NFR-15 | Portability | Full stack runs via `docker compose up` with zero prior setup |

---

## 5. DATA MODEL

### Entities

**User**
- id: UUID (PK)
- email: string (unique, indexed)
- hashed_password: string
- is_active: bool (default: true)
- is_deleted: bool (default: false)
- deleted_at: timestamp (nullable)
- created_at: timestamp
- updated_at: timestamp

**Todo**
- id: UUID (PK)
- user_id: UUID (FK → User, indexed)
- title: string (max 500 chars)
- description: text (nullable)
- status: enum [open, in_progress, done]
- priority: enum [low, medium, high]
- due_date: date (nullable)
- sort_order: integer (per-user, mutable)
- is_deleted: bool (default: false)
- deleted_at: timestamp (nullable)
- completed_at: timestamp (nullable)
- created_at: timestamp
- updated_at: timestamp

**Tag**
- id: UUID (PK)
- user_id: UUID (FK → User, indexed)
- name: string (max 50 chars, per-user unique)
- color: string (hex, default: #6366f1)
- created_at: timestamp

**TodoTag** (join table)
- todo_id: UUID (FK → Todo)
- tag_id: UUID (FK → Tag)
- (PK: todo_id + tag_id)

**RefreshToken**
- id: UUID (PK)
- user_id: UUID (FK → User, indexed)
- token_hash: string (SHA-256 of token, indexed)
- expires_at: timestamp
- revoked_at: timestamp (nullable)
- created_at: timestamp
- user_agent: string (nullable)
- ip_address: string (nullable)

---

## 6. API BOUNDARIES

### Base URL pattern
```
/api/v1/...
```

### Endpoints (summary)

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | /api/v1/auth/register | Create account | No |
| POST | /api/v1/auth/login | Issue tokens | No |
| POST | /api/v1/auth/refresh | Rotate access token | Cookie |
| POST | /api/v1/auth/logout | Revoke refresh token | Bearer |
| GET | /api/v1/auth/me | Current user profile | Bearer |
| GET | /api/v1/todos | List todos (filterable) | Bearer |
| POST | /api/v1/todos | Create todo | Bearer |
| GET | /api/v1/todos/{id} | Get todo | Bearer |
| PATCH | /api/v1/todos/{id} | Update todo | Bearer |
| DELETE | /api/v1/todos/{id} | Soft-delete todo | Bearer |
| POST | /api/v1/todos/{id}/restore | Restore soft-deleted | Bearer |
| DELETE | /api/v1/todos/{id}/permanent | Permanently delete | Bearer |
| POST | /api/v1/todos/reorder | Bulk reorder | Bearer |
| GET | /api/v1/tags | List user's tags | Bearer |
| POST | /api/v1/tags | Create tag | Bearer |
| PATCH | /api/v1/tags/{id} | Update tag | Bearer |
| DELETE | /api/v1/tags/{id} | Delete tag | Bearer |
| GET | /api/v1/health | Liveness probe | No |
| GET | /api/v1/ready | Readiness probe | No |

---

## 7. QUALITY GATES

### Gate A — Spec completeness (before implementation)
- [ ] spec-preflight score ≥ 0.85 across all 4 clarity dimensions
- [ ] All ADRs written and reviewed
- [ ] Threat model complete
- [ ] TLA+ spec designed (not yet checked)
- [ ] Architecture diagrams complete
- [ ] Scenarios written under `scenarios/` (never shown to coder)

### Gate B — Pre-merge (every PR)
- [ ] All tests pass (unit + integration + E2E)
- [ ] Coverage ≥95% lines, 100% on auth + data-access
- [ ] mypy/pyright strict — zero errors
- [ ] ESLint + TypeScript strict — zero errors
- [ ] Trivy: zero HIGH/CRITICAL CVEs
- [ ] Semgrep: zero security findings
- [ ] OWASP ZAP baseline: zero HIGH findings
- [ ] TLC model checker passes (if state machine changes)
- [ ] OpenAPI schema unchanged (or intentional version bump)

### Gate C — Production release
- [ ] Smoke test suite passes against staging
- [ ] Load test: p99 < 100ms at 50 RPS for 5 minutes
- [ ] Penetration test finding report reviewed
- [ ] Rollback procedure tested

---

## 8. CORRECTNESS PROPERTIES (TLA+)

The following invariants must hold under all interleavings:

1. **Ownership invariant**: A user can never read, modify, or delete another user's todo or tag
2. **Token validity invariant**: A revoked refresh token cannot be used to obtain a new access token
3. **Soft-delete invariant**: A soft-deleted todo is not returned in list/get operations but can be restored
4. **Status transition invariant**: Todo status transitions are monotonically valid per the allowed FSM
5. **Sort order invariant**: After any reorder operation, each user's todos have a unique, contiguous sort_order sequence
6. **Idempotency invariant**: Repeated identical create/update requests do not produce duplicate state changes

See `docs/formal-verification/tla-spec-design.md` for full TLA+ module design.
