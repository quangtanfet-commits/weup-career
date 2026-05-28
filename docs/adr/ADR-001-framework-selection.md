# ADR-001: Framework Selection

**Status:** Accepted  
**Date:** 2026-05-27  
**Deciders:** Engineering Team  

---

## Context

We need to select:
1. A **backend web framework** for the Python REST API
2. A **frontend UI library/framework** for the SPA

These are foundational choices that affect developer experience, performance, testing ergonomics, type safety, ecosystem health, and long-term maintainability.

---

## Backend: FastAPI

### Decision
Use **FastAPI** (Python 3.12) with **Uvicorn** ASGI server.

### Considered Alternatives

| Framework | Rationale for rejection |
|-----------|------------------------|
| Django REST Framework | Full-stack opinionated framework; heavier; ORM coupling; sync-first (async support added later but not idiomatic); more boilerplate for pure API use cases |
| Flask | No native async; no automatic request validation; no built-in OpenAPI generation; requires more manual wiring |
| Litestar | Excellent async-first alternative; less community momentum/ecosystem; smaller hiring pool |
| Starlette (raw) | FastAPI is built on Starlette — using FastAPI gives same performance with more DX |

### Arguments For FastAPI

**Performance:**
- ASGI-native: async request handling without thread-per-request overhead
- Benchmarks: comparable to NodeJS/Go for I/O bound workloads
- SQLite WAL + aiosqlite allows concurrent reads without blocking the event loop

**Developer experience:**
- Pydantic v2 integration: request validation, response serialization, and settings management from one library
- Automatic OpenAPI 3.1 documentation at `/docs` (Swagger UI) and `/redoc` — no manual schema authoring
- Type hints are the schema — Python type annotations drive everything
- Dependency injection is first-class — clean testability

**Production-readiness:**
- Used at scale by Uber, Netflix (Jupyter), Microsoft, and others
- Active maintenance (Tiangolo + FastAPI team)
- Native background task support
- Lifespan events for startup/shutdown hooks

**Testing:**
- `httpx.AsyncClient` with ASGI transport = full integration test without networking
- Dependency override pattern makes mocking trivial

### Consequences
- Async-first: all DB calls, external calls must be awaited; no blocking I/O in handlers
- Python 3.12 required (not 3.10/3.11)
- All repository methods must be `async def`

---

## Frontend: React + TypeScript + Vite

### Decision
Use **React 18** with **TypeScript 5** and **Vite 5** as the build tool.

### Considered Alternatives

| Library/Framework | Rationale for rejection |
|-------------------|------------------------|
| Vue 3 + Vite | Excellent alternative; engineering playbook's preferred frontend stack. Rejected here because React has a larger talent pool and the project scope doesn't require Vue-specific DX benefits (Composition API ≈ React hooks for this use case) |
| Next.js | Server-side rendering adds operational complexity (Node.js server required) for a use case that doesn't need SSR or SSG. Overkill for a logged-in-only SPA |
| SvelteKit | Less mature ecosystem; smaller community; fewer validated third-party component libraries |
| Angular | Verbose; heavy; enterprise-Java aesthetics; steep learning curve; overkill for small SPA |
| Plain Vanilla JS | No component model; scaling maintainability impossible; no type safety |

### Arguments For React

- **Ecosystem:** largest frontend ecosystem; most UI component libraries
- **TypeScript:** first-class TypeScript support; strict mode in this project
- **Testing:** Vitest + React Testing Library = fast, confidence-building tests
- **Hooks API:** clean composition model with `useState`, `useEffect`, `useCallback`
- **TanStack Query:** best server-state management available in any framework
- **DX:** Vite HMR is extremely fast (<50ms hot updates vs Webpack minutes)

### Arguments For Vite Over Create React App

- CRA is officially deprecated and unmaintained
- Vite: native ESM, sub-second cold start, <100ms HMR, Rollup production build
- Smaller config surface area; plugin ecosystem is mature
- Vitest integrates directly for consistent environment

### Consequences
- JSX/TSX: all components use TypeScript strict mode (no `any`, no implicit returns)
- No SSR in v1; CSR-only (impacts first-load time for unauthenticated users — acceptable since all content is behind login)
- Bundle size discipline: track with `rollup-plugin-visualizer`; target <250KB gzipped initial bundle

---

## Supporting Libraries

### Backend

| Library | Purpose | Version | Alternative rejected |
|---------|---------|---------|---------------------|
| SQLAlchemy 2.0 | ORM + query builder | 2.0.x | raw aiosqlite (no ORM abstraction); Tortoise ORM (less mature) |
| Alembic | DB migrations | 1.13.x | Manual SQL (not reproducible) |
| Pydantic v2 | Validation/serialization | 2.x | marshmallow (verbose); attrs (less integrated with FastAPI) |
| python-jose[cryptography] | JWT | 3.3.x | PyJWT (less feature-rich) |
| passlib[bcrypt] | Password hashing | 1.7.x | hashlib (too low-level; no bcrypt) |
| structlog | Structured logging | 24.x | loguru (less structured); stdlib logging (not JSON) |
| slowapi | Rate limiting | 0.1.x | Custom middleware (reinvents wheel) |

### Frontend

| Library | Purpose | Version | Alternative rejected |
|---------|---------|---------|---------------------|
| Zustand | Client state | 4.x | Redux (boilerplate); Jotai (less ergonomic for complex state); Context (perf issues) |
| TanStack Query | Server state | 5.x | SWR (less feature-rich); Apollo (GraphQL-specific) |
| React Hook Form + Zod | Forms + validation | 7.x + 3.x | Formik (slower, heavier); Yup (less type-safe than Zod) |
| Tailwind CSS | Styling | 3.x | Styled-components (runtime CSS-in-JS perf cost); CSS Modules (less DX) |
| Radix UI | Accessible primitives | 1.x | Headless UI (less comprehensive) |
| @dnd-kit/core | Drag-and-drop reorder | 6.x | react-beautiful-dnd (deprecated) |
| Framer Motion | Animations | 11.x | CSS transitions only (less control over list animations) |
| Axios | HTTP client | 1.x | fetch API (no interceptors out-of-the-box; less ergonomic retry) |
