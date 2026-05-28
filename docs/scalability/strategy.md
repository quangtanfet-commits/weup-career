# Scalability & Reliability Strategy

**Version:** 1.0.0 | **Date:** 2026-05-27

---

## Reliability Targets

| Tier | Metric | Target |
|------|--------|--------|
| Availability | Uptime per month | 99.9% (≤43 min/month downtime) |
| Latency | p50 read latency | <20ms |
| Latency | p99 read latency | <100ms |
| Latency | p99 write latency | <200ms |
| Error rate | 5xx errors | <0.1% of requests |
| Recovery | Time to recover from crash | <30 seconds |

---

## Failure Modes & Isolation

### Database Unavailability

- Backend catches SQLAlchemy `OperationalError` at repository level
- Maps to HTTP 503 `{"error": {"code": "SERVICE_UNAVAILABLE"}}`
- No stack trace exposed to client
- `/api/v1/ready` returns 503 → container orchestrator stops routing traffic
- SQLite process: DB locks release on process exit (no manual cleanup)

### Uvicorn Worker Crash

- Gunicorn (production) detects dead worker, respawns within 5s
- In-flight requests to dead worker → client sees TCP reset → client retries
- Other workers continue serving traffic (no full outage)
- Dev: single Uvicorn process; crash → Docker `restart: unless-stopped` policy

### Memory Pressure

- SQLAlchemy connection pool limits: `pool_size=5, max_overflow=10`
- Request body limit: 1MB (Nginx `client_max_body_size`)
- Response pagination: default 50 items, max 100 items — prevents OOM on large todo sets
- Container memory limit: 512MB (configurable via Docker Compose)

### File System Issues (SQLite)

- SQLite file on a Docker named volume (not ephemeral container layer)
- WAL mode: corruption recovery via `PRAGMA integrity_check`
- Backup: daily `cp app.db app.db.backup` via cron container
- Runbook: `docs/operations/runbook.md` covers recovery procedure

---

## Graceful Shutdown

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    logger.info("event", event="startup.complete")
    
    yield  # App runs here
    
    # Shutdown (triggered by SIGTERM)
    logger.info("event", event="shutdown.begin")
    await database.disconnect()    # Close all DB connections
    logger.info("event", event="shutdown.complete")
```

Nginx `proxy_read_timeout 300s` ensures no in-flight requests are dropped during a 60-second rolling restart window.

Docker Compose `stop_grace_period: 30s` gives the backend 30s to finish in-flight requests before SIGKILL.

---

## Database Abstraction Layer

### The Port Interface

```python
# app/todos/repository.py (Port — abstract interface)
class ITodoRepository(Protocol):
    async def create(self, user_id: UUID, data: TodoCreate) -> Todo: ...
    async def get(self, todo_id: UUID, user_id: UUID) -> Todo | None: ...
    async def list(self, user_id: UUID, filters: TodoFilters) -> PaginatedResult[Todo]: ...
    async def update(self, todo_id: UUID, user_id: UUID, data: TodoUpdate) -> Todo | None: ...
    async def soft_delete(self, todo_id: UUID, user_id: UUID) -> bool: ...
    async def restore(self, todo_id: UUID, user_id: UUID) -> bool: ...
    async def reorder(self, user_id: UUID, orders: list[TodoOrder]) -> bool: ...
```

### Current Adapter: SQLite via SQLAlchemy

```python
# app/todos/sql_repository.py (Adapter — SQLite)
class SQLAlchemyTodoRepository:
    def __init__(self, session: AsyncSession):
        self._session = session
    
    async def get(self, todo_id: UUID, user_id: UUID) -> Todo | None:
        result = await self._session.execute(
            select(TodoModel)
            .where(TodoModel.id == todo_id)
            .where(TodoModel.user_id == user_id)
            .where(TodoModel.is_deleted == False)
        )
        row = result.scalar_one_or_none()
        return Todo.from_orm(row) if row else None
```

### Future Adapter: PostgreSQL (zero app code changes)

To migrate to PostgreSQL:
1. `pip install asyncpg`
2. Change `DATABASE_URL=postgresql+asyncpg://user:pass@host/db`
3. Run `alembic upgrade head` on new DB
4. Deploy — identical application code

---

## Caching Design Points

### Current (v1): No server-side cache

At <50 concurrent users, SQLite with WAL is fast enough. Cache adds complexity and risk (stale data, invalidation bugs) that is unjustified.

TanStack Query provides client-side caching:
- `staleTime: 30000` (30s) — data considered fresh for 30s; no refetch
- `cacheTime: 300000` (5min) — cache retained for 5min after last subscriber
- Window focus triggers background refetch

### Phase 3: Server-side cache (Redis)

When we migrate to PostgreSQL + multi-node:

```
Request → Redis Cache (5min TTL) → PostgreSQL
              ↑
         Invalidated on any mutation
```

Cache keys:
- `todo:list:{user_id}:{filter_hash}` → paginated list results
- `todo:single:{todo_id}` → individual todo (invalidated on update)
- `tag:list:{user_id}` → tag list (rarely changes)

**The ITodoRepository interface accommodates caching as a decorator:**
```python
class CachingTodoRepository:
    def __init__(self, inner: ITodoRepository, cache: Redis):
        self._inner = inner
        self._cache = cache
    
    async def list(self, user_id: UUID, filters: TodoFilters) -> PaginatedResult[Todo]:
        key = f"todo:list:{user_id}:{hash(filters)}"
        cached = await self._cache.get(key)
        if cached:
            return deserialize(cached)
        result = await self._inner.list(user_id, filters)
        await self._cache.setex(key, 300, serialize(result))
        return result
```

---

## Async/Event-Driven Extension Points

The service layer emits domain events that can be consumed by subscribers in future:

```python
# Current: synchronous, no events
class TodoService:
    async def create_todo(self, ...) -> Todo:
        todo = await self.repo.create(...)
        # TODO: publish TodoCreated event (v2)
        return todo

# Future: event mesh
class TodoService:
    async def create_todo(self, ...) -> Todo:
        todo = await self.repo.create(...)
        await self.event_bus.publish(TodoCreated(todo_id=todo.id, user_id=todo.user_id))
        return todo
```

The event bus is injected via dependency injection — swappable between:
- `InMemoryEventBus` (tests, v1)
- `RedisEventBus` (Phase 3)
- `KafkaEventBus` (Phase 4, high-throughput)

---

## Retry Strategy

### Backend: Database Operations

```python
@retry(
    retry=retry_if_exception_type(OperationalError),
    wait=wait_exponential(multiplier=0.1, max=1),
    stop=stop_after_attempt(3),
    before_sleep=log_retry_attempt,
)
async def execute_with_retry(session, query):
    return await session.execute(query)
```

Only retry on transient errors (lock contention, timeout). Never retry on:
- Constraint violations (4xx — business logic error)
- Auth failures

### Frontend: API Requests

TanStack Query mutation retry:
```typescript
const createTodo = useMutation({
  mutationFn: apiClient.todos.create,
  retry: 1,                    // One retry on network error
  retryDelay: 1000,           // 1 second between retries
  onError: showErrorToast,    // After retry exhausted
})
```

Axios interceptor: auto-retry on 401 (after token refresh). Does NOT retry on 4xx (business errors).

---

## Backup & Recovery

| Component | Backup Strategy | RPO | RTO |
|-----------|----------------|-----|-----|
| SQLite DB | Daily cp to backup volume + weekly off-site | 24h | 30min |
| Docker images | Pushed to GHCR (immutable) | 0 (rebuild from git) | 5min |
| Secrets | Stored in secure notes + team password manager | 0 (rotate on recovery) | 10min |
| Config | In git repository | 0 (git history) | 5min |

See `docs/operations/runbook.md` for step-by-step recovery procedures.
