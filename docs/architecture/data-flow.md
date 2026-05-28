# Data Flow Diagrams

**Version:** 1.0.0 | **Date:** 2026-05-27

---

## System-Level Data Flow

```mermaid
flowchart TD
    subgraph "Client"
        BROWSER["Browser\n(User Actions)"]
        LOCALMEM["Memory\n(access_token)"]
        COOKIE["httpOnly Cookie\n(refresh_token)"]
    end

    subgraph "Nginx (Edge)"
        RATELIMIT["Rate Limiter\n(nginx lua / limit_req)"]
        STATICFILE["Static File Server\n(Frontend Bundle)"]
        PROXY["Reverse Proxy\n/api/* → backend:8000"]
        SECHEADERS["Security Headers\nCSP, HSTS, X-Frame"]
    end

    subgraph "Backend API"
        MIDDLEWARE["Middleware Stack\n- Correlation ID\n- Request timing\n- CORS\n- Trusted hosts"]
        AUTHDEP["Auth Dependency\nJWT validation\nuser injection"]
        HANDLER["Route Handler\nRequest validation\nResponse formatting"]
        SERVICE["Service Layer\nBusiness logic\nOwnership checks"]
        REPO["Repository Layer\nSQL queries\nData mapping"]
        LOGGER["Structured Logger\nNDJSON to stdout"]
    end

    subgraph "Persistence"
        SQLITE[("SQLite\nWAL mode\n- users\n- todos\n- tags\n- refresh_tokens")]
    end

    BROWSER -->|"HTTPS GET /\n(static assets)"| RATELIMIT
    RATELIMIT --> STATICFILE
    STATICFILE -->|"HTML/JS/CSS bundle"| BROWSER

    BROWSER -->|"HTTPS POST/GET /api/v1/*\nAuthorization: Bearer {token}"| RATELIMIT
    RATELIMIT --> SECHEADERS
    SECHEADERS --> PROXY
    PROXY --> MIDDLEWARE
    MIDDLEWARE --> AUTHDEP
    AUTHDEP -->|"current_user injected"| HANDLER
    HANDLER --> SERVICE
    SERVICE --> REPO
    REPO -->|"SQL via aiosqlite"| SQLITE
    SQLITE -->|"Rows / affected count"| REPO
    REPO -->|"Domain objects"| SERVICE
    SERVICE -->|"Results"| HANDLER
    HANDLER -->|"JSON response"| BROWSER

    MIDDLEWARE -->|"Log every request"| LOGGER
    HANDLER -->|"Log business events"| LOGGER

    BROWSER -->|"Stores token"| LOCALMEM
    BROWSER -->|"Cookie auto-sent"| COOKIE
```

---

## Authentication Data Flow

```mermaid
flowchart LR
    subgraph "Login Request"
        CREDS["email + password"]
    end

    subgraph "Backend — Auth Service"
        LOOKUP["DB lookup\nby email"]
        BCRYPT["bcrypt.checkpw\n(timing-safe)"]
        JWTGEN["JWT generation\n- sub: user_id\n- exp: +15min\n- jti: uuid\n- iss: todo-api"]
        RTGEN["Refresh token\n- random 32 bytes\n- SHA-256 hash\n- store hash only"]
    end

    subgraph "Response"
        BODY["JSON body:\naccess_token\nuser profile"]
        HCOOKIE["Set-Cookie:\nrefresh_token=...\nhttpOnly\nSecure\nSameSite=Strict\nPath=/api/v1/auth/refresh\nMax-Age=604800 (7d)"]
    end

    subgraph "Client Storage"
        MEM["In-memory (Zustand)\naccess_token\n(cleared on page close)"]
        BROWSER_COOKIE["Browser httpOnly cookie\n(inaccessible to JS)"]
    end

    CREDS --> LOOKUP --> BCRYPT --> JWTGEN & RTGEN
    JWTGEN --> BODY
    RTGEN --> HCOOKIE
    BODY --> MEM
    HCOOKIE --> BROWSER_COOKIE
```

---

## Todo Query Data Flow (List with Filters)

```mermaid
flowchart TD
    subgraph "Frontend"
        FILTERBAR["Filter Bar Component\n- status dropdown\n- priority filter\n- tag multi-select\n- search text\n- due date range"]
        QUERYPARAMS["URL Query Params\n?status=open&tag=work\n&search=meeting&priority=high"]
        TANSTACK["TanStack Query\ncacheKey: ['todos', filters]\nstaleTime: 30s\ncacheTime: 5min"]
        SKELETON["Skeleton Loader\n(shown during fetch)"]
    end

    subgraph "Network"
        REQUEST["GET /api/v1/todos\n?status=open\n&priority=high\n&tag_ids=uuid1,uuid2\n&search=meeting\n&page=1&per_page=50\n&sort=sort_order"]
    end

    subgraph "Backend"
        PARSE["Parse + validate\nquery params\n(Pydantic model)"]
        AUTHCHECK["Inject current_user\nfrom JWT"]
        QUERY["SQLAlchemy query\nWHERE user_id = ?\nAND is_deleted = false\nAND status IN (?)\nAND priority = ?\nAND title LIKE ?\nJOIN todo_tags...\nORDER BY sort_order\nLIMIT ? OFFSET ?"]
        COUNT["COUNT(*) for total\n(same filters, no pagination)"]
        RESPONSE["PaginatedResponse\n{items, total, page, per_page}"]
    end

    FILTERBAR -->|"debounced 300ms"| QUERYPARAMS
    QUERYPARAMS --> TANSTACK
    TANSTACK --> SKELETON
    TANSTACK --> REQUEST
    REQUEST --> PARSE
    PARSE --> AUTHCHECK
    AUTHCHECK --> QUERY & COUNT
    QUERY --> RESPONSE
    COUNT --> RESPONSE
    RESPONSE --> TANSTACK
    TANSTACK --> FILTERBAR
```

---

## Request Correlation & Observability Data Flow

```mermaid
flowchart LR
    subgraph "Nginx"
        GEN_ID["Generate\nX-Request-ID\n(if not present)"]
    end

    subgraph "Backend Middleware"
        EXTRACT["Extract X-Request-ID\nfrom headers"]
        BIND["Bind to structlog\ncontext variables:\n- request_id\n- user_id (post-auth)\n- path\n- method"]
    end

    subgraph "Log Pipeline"
        STRUCTLOG["structlog\nJSON formatter"]
        STDOUT["stdout\n(NDJSON stream)"]
        LOGSHIP["Log shipper\n(e.g. Vector / Fluentd)\nfuture"]
        ELASTIC["Elasticsearch /\nLoki (future)"]
    end

    subgraph "Response"
        RESP_HEADER["Response header\nX-Request-ID: req_xxx"]
    end

    GEN_ID --> EXTRACT
    EXTRACT --> BIND
    BIND -->|"Every log.info/error\ninherits context"| STRUCTLOG
    STRUCTLOG --> STDOUT
    STDOUT --> LOGSHIP
    LOGSHIP --> ELASTIC
    BIND --> RESP_HEADER
```

---

## Soft Delete & Recovery Data Flow

```mermaid
flowchart TD
    subgraph "User Action"
        DELETE_BTN["User clicks Delete"]
    end

    subgraph "Frontend"
        OPT_HIDE["Optimistically hide\nfrom list (instant)"]
        UNDO_TOAST["Show undo toast\n(5 second timer)"]
        API_CALL["DELETE /api/v1/todos/{id}"]
    end

    subgraph "Backend"
        SOFTDEL["UPDATE todo\nSET is_deleted=true\ndeleted_at=NOW()\nWHERE id=? AND user_id=?"]
        NOTE1["Todo NOT returned\nin list queries\n(WHERE is_deleted=false)"]
    end

    subgraph "Recovery Window (30 days)"
        RESTORE_BTN["User clicks Undo\nor visits /trash"]
        RESTORE_API["POST /api/v1/todos/{id}/restore"]
        RESTORE_DB["UPDATE todo\nSET is_deleted=false\ndeleted_at=NULL"]
    end

    subgraph "Purge Job (daily cron)"
        PURGE["DELETE FROM todo\nWHERE is_deleted=true\nAND deleted_at < NOW()-30days"]
    end

    DELETE_BTN --> OPT_HIDE & UNDO_TOAST
    DELETE_BTN --> API_CALL
    API_CALL --> SOFTDEL --> NOTE1

    UNDO_TOAST --> RESTORE_BTN
    RESTORE_BTN --> RESTORE_API --> RESTORE_DB

    NOTE1 --> PURGE
```
