# ADR-003: API Style

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Context

The frontend SPA communicates with the backend. We need to decide the API contract style.

---

## Decision

**Use REST over HTTP/JSON, documented with OpenAPI 3.1, versioned under `/api/v1/`.**

---

## Rationale

### REST vs GraphQL vs tRPC vs gRPC

| Style | Verdict | Reason |
|-------|---------|--------|
| **REST + JSON** | ✅ Selected | Industry standard; every HTTP client can consume it; trivial to curl/debug; FastAPI generates OpenAPI automatically; excellent caching semantics; simple to test |
| GraphQL | ❌ Rejected | Overkill cho data model này; client library riêng; N+1 dồn về backend; khó curl-debug. (REST cũng dễ đặt **Consent Guard/audit** tập trung theo route hơn) |
| tRPC | ❌ Rejected | TypeScript-only coupling — breaks the clean backend/frontend separation; harder to integrate external clients; not framework-agnostic |
| gRPC | ❌ Rejected | Binary protocol; no browser-native support (requires grpc-web proxy); complex toolchain; wrong abstraction level for a web SPA |

### REST Design Rules

**Resource naming:**
- Nouns, plural: `/assessments`, `/careers`, `/competencies`, `/recommendations`, `/guardians`, `/users`
- Sub-resources: `/school/{id}/students`, `/me/assessments/{id}`
- Action as noun khi cần: `/assessments/{type}/submit`, `/recommendations/{id}/confirm`, `/guardians/consent/revoke`

**Idempotency:**
- GET: idempotent, cacheable
- POST: not idempotent (creates resource); returns 201 + Location header
- PATCH: partial update (not PUT — avoids full-replace semantics)
- DELETE: idempotent (second delete returns 404, not error)

**Versioning strategy:**
- URL path prefix: `/api/v1/` 
- Breaking changes bump `/api/v2/` with 6-month deprecation window
- Non-breaking additions (new optional fields) do not require version bump

**Pagination:**
- Cursor-based for large datasets (future); offset-based for v1 (simpler)
- Response envelope: `{"items": [...], "total": N, "page": P, "per_page": K}`
- Default `per_page=50`, max `per_page=100`

**Content negotiation:**
- Always `Content-Type: application/json`
- No XML support

### OpenAPI 3.1 Contract

- FastAPI auto-generates from Python type hints — schema is always in sync with code
- Schema published at `/api/v1/openapi.json`
- Used for: frontend type generation, integration tests, external client SDKs
- Validated in CI: `openapi-spec-validator` — schema must be valid before merge

### CORS Policy

- In development: `*` allowed (dev convenience)
- In production: explicit allow-list (exact frontend origin only)
- Preflight cached: `Access-Control-Max-Age: 600`

---

## Consequences

- Typed API client in frontend is auto-generated from OpenAPI schema via `openapi-typescript`
- All response types are explicitly typed — no `any` in API responses
- Backend schema changes automatically surface as TypeScript compile errors on frontend
