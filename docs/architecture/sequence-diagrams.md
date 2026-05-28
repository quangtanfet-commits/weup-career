# Sequence Diagrams

**Version:** 1.0.0 | **Date:** 2026-05-27

---

## Auth Flow — Register

```mermaid
sequenceDiagram
    autonumber
    actor U as User (Browser)
    participant FE as Frontend SPA
    participant N as Nginx
    participant API as Backend API
    participant DB as SQLite

    U->>FE: Fill registration form
    FE->>FE: Validate with Zod schema (client-side)
    FE->>N: POST /api/v1/auth/register {email, password}
    N->>API: Proxy request (X-Request-ID injected by Nginx)
    API->>API: Validate request body (Pydantic)
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: NULL (email available)
    API->>API: Hash password with bcrypt (cost=12)
    API->>DB: INSERT user
    DB-->>API: User record
    API-->>N: 201 Created {id, email, created_at}
    N-->>FE: 201 Created
    FE->>FE: Auto-login: POST /auth/login
    FE-->>U: Redirect to /todos
```

---

## Auth Flow — Login & Token Issuance

```mermaid
sequenceDiagram
    autonumber
    actor U as User (Browser)
    participant FE as Frontend SPA
    participant API as Backend API
    participant DB as SQLite

    U->>FE: Submit login form (email, password)
    FE->>API: POST /api/v1/auth/login
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: User row (or null)

    alt User not found or inactive
        API-->>FE: 401 {code: INVALID_CREDENTIALS}
        FE-->>U: "Invalid email or password" (generic — no enumeration)
    else Valid credentials
        API->>API: bcrypt.checkpw(password, hash)
        alt Password mismatch
            API-->>FE: 401 {code: INVALID_CREDENTIALS}
        else Password correct
            API->>API: Create access_token JWT (exp: 15min)
            API->>API: Create refresh_token (random UUID)
            API->>DB: INSERT refresh_token (hash, user_id, exp)
            API-->>FE: 200 {access_token, user}\n Set-Cookie: refresh_token=... (httpOnly, Secure, SameSite=Strict)
            FE->>FE: Store access_token in memory (Zustand)
            FE-->>U: Redirect to /todos
        end
    end
```

---

## Auth Flow — Silent Token Refresh

```mermaid
sequenceDiagram
    autonumber
    participant FE as Frontend (Axios interceptor)
    participant API as Backend API
    participant DB as SQLite

    Note over FE: Timer fires 60s before access_token expiry
    FE->>API: POST /api/v1/auth/refresh (Cookie: refresh_token)
    API->>API: Extract refresh_token from httpOnly cookie
    API->>API: SHA-256 hash the token value
    API->>DB: SELECT refresh_token WHERE hash = ? AND revoked_at IS NULL AND expires_at > NOW()
    
    alt Token valid
        DB-->>API: Token record
        API->>DB: UPDATE refresh_token SET revoked_at = NOW() (rotate — old token dead)
        API->>API: Create new refresh_token
        API->>DB: INSERT new refresh_token
        API->>API: Create new access_token JWT
        API-->>FE: 200 {access_token}\nSet-Cookie: new refresh_token
        FE->>FE: Update Zustand store with new access_token
    else Token expired or revoked
        API-->>FE: 401 {code: TOKEN_EXPIRED}
        FE->>FE: Clear auth state
        FE->>FE: Redirect to /login
    end
```

---

## Auth Flow — 401 Interceptor (Request Mid-Flight)

```mermaid
sequenceDiagram
    autonumber
    participant Component as React Component
    participant Query as TanStack Query
    participant Axios as Axios Interceptor
    participant API as Backend API

    Component->>Query: useQuery('todos')
    Query->>Axios: GET /api/v1/todos (Bearer: expired_token)
    Axios->>API: Request with expired JWT
    API-->>Axios: 401 {code: TOKEN_EXPIRED}
    
    Note over Axios: Intercept 401 — attempt silent refresh
    Axios->>API: POST /api/v1/auth/refresh (cookie)
    
    alt Refresh success
        API-->>Axios: 200 {access_token}
        Axios->>Axios: Update token in memory
        Axios->>API: Retry original request with new token
        API-->>Axios: 200 {todos}
        Axios-->>Query: Success response
        Query-->>Component: Updated data
    else Refresh failed
        API-->>Axios: 401
        Axios->>Axios: Clear auth state
        Axios->>Axios: Redirect to /login
    end
```

---

## Todo CRUD — Create with Optimistic Update

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant FE as Frontend
    participant Query as TanStack Query
    participant API as Backend API
    participant DB as SQLite

    U->>FE: Click "Add Todo", fill form, submit
    FE->>Query: mutate(createTodo, {title, ...})
    
    Note over Query: Optimistic update BEFORE network call
    Query->>Query: Cancel in-flight queries for 'todos'
    Query->>Query: Snapshot current todos cache
    Query->>Query: Inject optimistic todo (temp ID, status=open)
    Query-->>FE: Re-render with optimistic item (instant feedback)
    
    Query->>API: POST /api/v1/todos {title, description, priority, due_date}
    API->>API: Validate request body
    API->>API: Verify user ownership context
    API->>DB: INSERT todo (sort_order = max + 1)
    DB-->>API: Todo record with real UUID
    API-->>Query: 201 {todo}
    
    alt Success
        Query->>Query: Replace optimistic item with real item
        Query->>Query: Invalidate todos cache → background refetch
    else Network/Server Error
        Query->>Query: Rollback to snapshot (remove optimistic item)
        Query-->>FE: Show error toast
    end
```

---

## Todo Reorder (Drag-and-Drop)

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant DnD as DnD Library (@dnd-kit)
    participant Store as Zustand Store
    participant Query as TanStack Query
    participant API as Backend API

    U->>DnD: Drag todo item to new position
    DnD->>Store: onDragEnd → compute new order array
    Store->>Store: Reorder items in local state (instant visual)
    Store->>Query: mutate(reorderTodos, [{id, sort_order}...])
    Query->>API: POST /api/v1/todos/reorder [{id, sort_order}...]
    
    alt Success
        API->>API: Validate all IDs belong to user
        API-->>API: Bulk UPDATE sort_order (transaction)
        API-->>Query: 200 OK
        Query->>Query: Invalidate 'todos' cache
    else Failure
        API-->>Query: 400/500
        Query-->>Store: Rollback to previous order
        Store-->>DnD: Re-render with original order
    end
```

---

## Soft Delete & Restore Flow

```mermaid
sequenceDiagram
    autonumber
    actor U as User
    participant FE as Frontend
    participant API as Backend API
    participant DB as SQLite

    U->>FE: Click delete on todo
    FE->>FE: Show undo toast with 5s timer
    FE->>API: DELETE /api/v1/todos/{id}
    API->>DB: UPDATE todo SET is_deleted=true, deleted_at=NOW()
    DB-->>API: Affected rows = 1
    API-->>FE: 204 No Content
    FE->>FE: Remove item from list (optimistic already done)

    alt User clicks "Undo" within 5 seconds
        FE->>API: POST /api/v1/todos/{id}/restore
        API->>DB: UPDATE todo SET is_deleted=false, deleted_at=NULL
        DB-->>API: Affected rows = 1
        API-->>FE: 200 {todo}
        FE->>FE: Re-add todo to list
        FE-->>U: Undo confirmed
    else Timer expires
        FE->>FE: Dismiss toast
        Note over DB: Todo remains soft-deleted\nPurge job removes after 30 days
    end
```

---

## Health & Readiness Check

```mermaid
sequenceDiagram
    participant Orchestrator as Container Orchestrator
    participant API as Backend API
    participant DB as SQLite

    loop Every 10 seconds (liveness)
        Orchestrator->>API: GET /api/v1/health
        API-->>Orchestrator: 200 {status: "ok", uptime_s: 1234}
    end

    loop Every 5 seconds (readiness)
        Orchestrator->>API: GET /api/v1/ready
        API->>DB: SELECT 1 (lightweight ping)
        alt DB responsive
            DB-->>API: 1
            API-->>Orchestrator: 200 {status: "ready", db: "ok"}
        else DB not responding
            API-->>Orchestrator: 503 {status: "not_ready", db: "error"}
            Note over Orchestrator: Do NOT send traffic; restart if persistent
        end
    end
```
