# System Architecture Overview

**Version:** 1.0.0 | **Status:** APPROVED FOR REVIEW | **Date:** 2026-05-27

---

## C4 Model

### Level 1 — System Context

```mermaid
C4Context
    title System Context — Todo Application

    Person(user, "User", "A person who manages their tasks via the web UI")
    Person(operator, "Operator", "DevOps/SRE managing the deployment")

    System(todoApp, "Todo Application", "Allows users to create and manage todo items with tagging, priorities, due dates, and search")

    System_Ext(dockerRegistry, "Container Registry", "Stores built Docker images (GHCR / Docker Hub)")
    System_Ext(ciSystem, "GitHub Actions", "Runs automated quality gates and deployment pipelines")
    System_Ext(smtp, "SMTP (future)", "Password-reset email delivery — deferred to v2")

    Rel(user, todoApp, "Uses", "HTTPS / Browser")
    Rel(operator, todoApp, "Deploys, monitors", "SSH / Docker CLI / docker compose")
    Rel(ciSystem, dockerRegistry, "Pushes images to")
    Rel(ciSystem, todoApp, "Deploys to staging / production")
    Rel(todoApp, smtp, "Sends reset emails (v2)", "SMTP")
```

---

### Level 2 — Container Diagram

```mermaid
C4Container
    title Container Diagram — Todo Application

    Person(user, "User", "Web browser")

    Container(nginx, "Nginx Reverse Proxy", "nginx:alpine", "TLS termination, static file serving, /api upstream routing, rate limiting at L7")
    Container(frontend, "Frontend SPA", "React 18 / TypeScript / Vite", "Single-page app bundle served as static files; communicates with backend via REST + JSON")
    Container(backend, "Backend API", "Python 3.12 / FastAPI / Uvicorn", "RESTful API; JWT authentication; business logic; database access via async SQLAlchemy")
    ContainerDb(database, "SQLite Database", "SQLite 3.45 / aiosqlite", "Persistent storage; single file; WAL mode for concurrent reads; abstracted behind SQLAlchemy for future migration")

    Rel(user, nginx, "HTTPS requests", "TLS 1.3")
    Rel(nginx, frontend, "Serves static assets", "file system")
    Rel(nginx, backend, "Proxies /api/* requests", "HTTP (internal Docker network)")
    Rel(backend, database, "Reads / writes", "SQLAlchemy async / aiosqlite")
```

---

### Level 3 — Component Diagram — Backend API

```mermaid
C4Component
    title Component Diagram — Backend API (FastAPI)

    Container_Boundary(api, "Backend API") {
        Component(router, "API Router", "FastAPI Routers", "Routes requests to correct handler; includes versioning prefix /api/v1")
        Component(authMiddleware, "Auth Middleware", "FastAPI dependency injection", "Validates Bearer JWT on protected routes; injects current_user into handler context")
        Component(rateLimiter, "Rate Limiter", "slowapi + Redis-compatible in-memory", "Enforces per-IP and per-user rate limits")
        Component(authHandler, "Auth Handler", "auth/router.py", "Register, login, logout, token refresh, /me")
        Component(todoHandler, "Todo Handler", "todos/router.py", "CRUD + reorder + soft-delete/restore endpoints")
        Component(tagHandler, "Tag Handler", "tags/router.py", "Tag CRUD endpoints")
        Component(authService, "Auth Service", "auth/service.py", "Token issuance, validation, rotation, revocation; password hashing")
        Component(todoService, "Todo Service", "todos/service.py", "Business logic; ownership validation; sort order management")
        Component(tagService, "Tag Service", "tags/service.py", "Tag lifecycle; uniqueness enforcement per user")
        Component(userRepo, "User Repository", "users/repository.py", "User CRUD against SQLAlchemy models")
        Component(todoRepo, "Todo Repository", "todos/repository.py", "Todo queries; soft-delete filter; pagination; search")
        Component(tagRepo, "Tag Repository", "tags/repository.py", "Tag + TodoTag join operations")
        Component(tokenRepo, "Token Repository", "auth/token_repository.py", "Refresh token persistence and revocation")
        Component(db, "Database Session", "core/database.py", "AsyncSession factory; transaction management; connection pool")
        Component(logger, "Structured Logger", "core/logging.py", "structlog + JSON formatter; correlation ID injection")
    }

    Rel(router, authMiddleware, "Depends on")
    Rel(router, rateLimiter, "Depends on")
    Rel(router, authHandler, "Routes to")
    Rel(router, todoHandler, "Routes to")
    Rel(router, tagHandler, "Routes to")
    Rel(authHandler, authService, "Uses")
    Rel(todoHandler, todoService, "Uses")
    Rel(tagHandler, tagService, "Uses")
    Rel(authService, userRepo, "Uses")
    Rel(authService, tokenRepo, "Uses")
    Rel(todoService, todoRepo, "Uses")
    Rel(tagService, tagRepo, "Uses")
    Rel(userRepo, db, "Uses")
    Rel(todoRepo, db, "Uses")
    Rel(tagRepo, db, "Uses")
    Rel(tokenRepo, db, "Uses")
```

---

### Level 3 — Component Diagram — Frontend SPA

```mermaid
C4Component
    title Component Diagram — Frontend SPA (React)

    Container_Boundary(spa, "Frontend SPA") {
        Component(router, "React Router", "react-router-dom v6", "Client-side routing; protected route guards; redirect to /login if unauthenticated")
        Component(authStore, "Auth Store", "Zustand + persist", "Access token in memory; refresh token in httpOnly cookie; auto-refresh timer")
        Component(todoStore, "Todo Store", "Zustand + immer", "Optimistic update state; pending operations queue")
        Component(apiClient, "API Client", "Axios + interceptors", "Base URL config; Bearer token injection; 401 → token refresh → retry; correlation ID header")
        Component(queryLayer, "Query Layer", "TanStack Query v5", "Server state cache; background refetch; stale-while-revalidate; mutations with rollback")
        Component(authPages, "Auth Pages", "LoginPage / RegisterPage", "Form validation via react-hook-form + Zod; error display")
        Component(todoPage, "Todo Page", "TodoPage / TodoList / TodoItem", "Main workspace; filter bar; drag-and-drop reorder; optimistic updates")
        Component(tagManager, "Tag Manager", "TagManager / TagPill", "Inline tag creation; multi-select filter by tag")
        Component(designSystem, "Design System", "Tailwind CSS + Radix UI", "Accessible components; theme tokens; responsive utilities")
        Component(animations, "Animations", "Framer Motion", "List enter/exit; micro-interactions; skeleton loaders")
    }

    Rel(router, authPages, "Renders on /login /register")
    Rel(router, todoPage, "Renders on / (protected)")
    Rel(router, authStore, "Reads auth state for guards")
    Rel(todoPage, queryLayer, "useQuery / useMutation")
    Rel(todoPage, todoStore, "Optimistic state")
    Rel(todoPage, tagManager, "Renders inside")
    Rel(queryLayer, apiClient, "HTTP calls")
    Rel(authPages, apiClient, "HTTP calls")
    Rel(apiClient, authStore, "Reads/writes tokens")
    Rel(todoPage, designSystem, "Uses components")
    Rel(todoPage, animations, "Uses")
```

---

## Frontend Architecture Detail

### Directory Structure

```
frontend/
├── src/
│   ├── api/            # Axios client + all API functions (typed)
│   ├── components/     # Reusable UI components (design system layer)
│   ├── features/       # Feature modules (auth/, todos/, tags/)
│   │   ├── auth/       # Login, Register, AuthGuard
│   │   ├── todos/      # TodoList, TodoItem, CreateTodoForm, FilterBar
│   │   └── tags/       # TagManager, TagPill, TagFilter
│   ├── hooks/          # Custom React hooks
│   ├── pages/          # Route-level page components
│   ├── store/          # Zustand stores (auth, todo)
│   ├── types/          # TypeScript type definitions (shared with API)
│   ├── lib/            # Utilities (date formatting, validation schemas)
│   └── main.tsx        # App entry point
├── public/
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── vitest.config.ts
└── playwright.config.ts
```

### State Management Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Component Tree                  │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  Auth Store  │    │      TanStack Query Cache    │   │
│  │  (Zustand)   │    │  [todos, tags, user profile] │   │
│  │              │    │  stale-while-revalidate       │   │
│  │ - token      │    │  optimistic mutations         │   │
│  │ - user       │    │  background sync              │   │
│  │ - isLoading  │    └──────────────┬───────────────┘   │
│  └──────┬───────┘                   │                   │
│         │                           ▼                   │
│         └──────────► Axios API Client ──► Backend API   │
└─────────────────────────────────────────────────────────┘
```

**Design principle:** Server state (todo data) lives in TanStack Query. Client-only state (auth tokens, UI preferences) lives in Zustand. No duplication.

---

## Backend Architecture Detail

### Hexagonal Architecture (Ports & Adapters)

```
┌──────────────────────────────────────────────────────────────┐
│                        HTTP Layer (FastAPI)                   │
│  Request → Validation → Dependency Injection → Handler       │
└────────────────────────┬─────────────────────────────────────┘
                         │ calls
┌────────────────────────▼─────────────────────────────────────┐
│                      Service Layer                           │
│  (Business Logic — no framework imports, pure Python)        │
│                                                              │
│  AuthService  │  TodoService  │  TagService                  │
└────────────────────────┬─────────────────────────────────────┘
                         │ calls (via Port interface)
┌────────────────────────▼─────────────────────────────────────┐
│                    Repository Layer (Port)                    │
│  Abstract base classes; injectable; testable with in-memory  │
│                                                              │
│  IUserRepo  │  ITodoRepo  │  ITagRepo  │  ITokenRepo         │
└────────────────────────┬─────────────────────────────────────┘
                         │ implemented by
┌────────────────────────▼─────────────────────────────────────┐
│              SQLAlchemy Adapters (Adapter Layer)             │
│  Concrete SQLAlchemy implementations; SQLite today           │
│  Swap to Postgres by changing the adapter + connection URL   │
└──────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
backend/
├── app/
│   ├── main.py             # FastAPI app factory
│   ├── core/
│   │   ├── config.py       # Pydantic settings (env vars)
│   │   ├── database.py     # AsyncSession factory, lifespan
│   │   ├── security.py     # JWT encoding/decoding, password hashing
│   │   ├── logging.py      # structlog configuration
│   │   ├── middleware.py   # Correlation ID, request timing
│   │   └── exceptions.py  # Custom exception hierarchy
│   ├── auth/
│   │   ├── router.py       # /auth/* endpoints
│   │   ├── service.py      # Token lifecycle, auth logic
│   │   ├── models.py       # SQLAlchemy: User, RefreshToken
│   │   ├── schemas.py      # Pydantic request/response schemas
│   │   ├── repository.py   # UserRepo, TokenRepo (abstract + SQL)
│   │   └── dependencies.py # get_current_user, require_active
│   ├── todos/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py       # SQLAlchemy: Todo
│   │   ├── schemas.py
│   │   └── repository.py
│   ├── tags/
│   │   ├── router.py
│   │   ├── service.py
│   │   ├── models.py       # SQLAlchemy: Tag, TodoTag
│   │   ├── schemas.py
│   │   └── repository.py
│   └── api/
│       └── v1/router.py    # Master router (includes all sub-routers)
├── migrations/             # Alembic
│   ├── env.py
│   └── versions/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml
└── Dockerfile
```

---

## Database Design

### Entity-Relationship Diagram

```mermaid
erDiagram
    USER {
        uuid id PK
        string email UK
        string hashed_password
        bool is_active
        bool is_deleted
        timestamp deleted_at
        timestamp created_at
        timestamp updated_at
    }
    TODO {
        uuid id PK
        uuid user_id FK
        string title
        text description
        enum status
        enum priority
        date due_date
        int sort_order
        bool is_deleted
        timestamp deleted_at
        timestamp completed_at
        timestamp created_at
        timestamp updated_at
    }
    TAG {
        uuid id PK
        uuid user_id FK
        string name
        string color
        timestamp created_at
    }
    TODOTAG {
        uuid todo_id FK
        uuid tag_id FK
    }
    REFRESH_TOKEN {
        uuid id PK
        uuid user_id FK
        string token_hash UK
        timestamp expires_at
        timestamp revoked_at
        timestamp created_at
        string user_agent
        string ip_address
    }

    USER ||--o{ TODO : "owns"
    USER ||--o{ TAG : "owns"
    USER ||--o{ REFRESH_TOKEN : "has"
    TODO }o--o{ TAG : "TODOTAG"
```

### Index Strategy

| Table | Index | Type | Reason |
|-------|-------|------|--------|
| user | email | UNIQUE | Login lookup |
| todo | user_id, is_deleted, sort_order | COMPOSITE | List query hot path |
| todo | user_id, status | COMPOSITE | Filter by status |
| todo | user_id, due_date | COMPOSITE | Due date range filter |
| tag | user_id, name | UNIQUE | Per-user uniqueness |
| refresh_token | token_hash | UNIQUE | Token validation |
| refresh_token | user_id, revoked_at | COMPOSITE | Active token lookup |

---

## Error Handling Strategy

### Error Response Schema

```json
{
  "error": {
    "code": "TODO_NOT_FOUND",
    "message": "Todo with id 'abc' not found",
    "details": {},
    "request_id": "req_01HX..."
  }
}
```

### HTTP Status Code Map

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PATCH |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation error (Pydantic) |
| 401 | Unauthorized | Missing/invalid/expired access token |
| 403 | Forbidden | Valid token but insufficient permission |
| 404 | Not Found | Resource doesn't exist or not owned |
| 409 | Conflict | Duplicate email on register; duplicate tag name |
| 422 | Unprocessable Entity | Schema error with field-level details |
| 429 | Too Many Requests | Rate limit exceeded (Retry-After header) |
| 500 | Internal Server Error | Unexpected; no stack trace exposed |
| 503 | Service Unavailable | Database unavailable (readiness check) |

### Error Boundary Architecture (Frontend)

```
App
└── ErrorBoundary (catches unhandled React errors → fallback UI)
    └── QueryClientProvider
        └── TanStack Query errors → toast notifications
            └── Axios interceptors → 401 → token refresh → retry
                └── 401 again → logout + redirect /login
```

---

## Observability Strategy

### Structured Log Format

Every log line is NDJSON:

```json
{
  "timestamp": "2026-05-27T10:00:00.000Z",
  "level": "info",
  "service": "todo-api",
  "version": "1.0.0",
  "request_id": "req_01HX...",
  "user_id": "usr_01HX...",
  "method": "POST",
  "path": "/api/v1/todos",
  "status_code": 201,
  "duration_ms": 12,
  "event": "request.completed"
}
```

### Log Levels

| Level | Use |
|-------|-----|
| DEBUG | DB query details, token contents (dev only — never in prod) |
| INFO | Request in/out, business events (todo created, user registered) |
| WARNING | Rate limit approached, slow query (>50ms), token nearing expiry |
| ERROR | Unhandled exception; DB error; auth failure |

### Metrics (future-ready)

Expose `/metrics` endpoint (Prometheus format) via `prometheus-fastapi-instrumentator`:
- `http_requests_total` (method, path, status)
- `http_request_duration_seconds` (histogram)
- `active_users_gauge`
- `todo_operations_total` (operation type)
