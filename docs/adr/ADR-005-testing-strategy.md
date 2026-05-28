# ADR-005: Testing Strategy

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Decision

Use a multi-layer testing strategy targeting ≥95% meaningful line coverage, with 100% coverage required for auth and data-access layers.

Full details in `docs/testing/strategy.md`. This ADR captures the rationale for key decisions.

---

## Backend Testing Stack

**pytest + pytest-asyncio + httpx.AsyncClient**

- `pytest-asyncio` handles async test functions natively
- `httpx.AsyncClient` with `ASGITransport` = full integration tests with zero network overhead
- No separate test DB server needed: use SQLite in-memory per test (`sqlite+aiosqlite:///:memory:`)
- Each test gets a fresh DB via a fixture that runs Alembic migrations in-memory at test start

**Why not `pytest-django` / TestClient:**
- Not applicable (no Django)
- `httpx.AsyncClient` is the idiomatic FastAPI testing approach (recommended in official docs)

**Property-based testing with Hypothesis:**
- 10,000+ cases for auth service (password hashing, token generation)
- Fuzz todo title/description inputs for SQL injection safety

**Coverage tool: pytest-cov + coverage.py**
- `--cov-fail-under=95` enforced in CI
- Branch coverage enabled
- `[tool.coverage.report] exclude_lines` lists non-coverage-worthy patterns (Protocol, TYPE_CHECKING, etc.)

---

## Frontend Testing Stack

**Vitest + React Testing Library + MSW**

**Why Vitest over Jest:**
- Same API as Jest but runs in Vite context — no separate Babel transform
- 5-10x faster than Jest for this stack
- `expect`, `describe`, `it`, `vi.fn()` — identical API surface

**React Testing Library philosophy:**
- Test behavior, not implementation
- `getByRole`, `getByLabelText` — accessibility-first queries
- No `wrapper.find('.className')` — no testing implementation details

**MSW (Mock Service Worker) for API mocking:**
- Intercepts actual Axios HTTP calls at the network level (no mocking `axios.get`)
- Same MSW handlers used in both unit tests (Node) and browser E2E (service worker)
- Realistic: tests fail if the API call changes signature

---

## E2E Testing: Playwright

**Why Playwright over Cypress:**
- Multi-browser: Chromium, Firefox, WebKit in one suite
- Async-native: no command queue (unlike Cypress's chainable API)
- Component testing support (future)
- Better parallelism
- No iframe restrictions

**E2E test scope:**
- Critical user flows only (happy path + key error paths)
- Not exhaustive unit-test duplication
- Runs against real docker-compose stack in CI

---

## Consequences

- Every feature branch must pass all test layers before merge
- Test fixtures are fixtures, not mocks (prefer real behaviour where possible)
- Snapshot tests are prohibited (they break for cosmetic reasons; not meaningful coverage)
- `*.test.ts` colocated with implementation files; not in a separate `__tests__` directory
