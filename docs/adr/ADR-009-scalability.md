# ADR-009: Scalability Approach

**Status:** Accepted  
**Date:** 2026-05-27  

---

## Decision

Design for **horizontal scalability from the start** while deploying on a **single node with SQLite** initially. The abstraction layer ensures zero application-code changes during the scale-up path.

---

## Scale-Up Path

### Phase 1: Single node, SQLite (current)

```
Nginx (1) → Uvicorn (1 process) → SQLite (WAL)
```

- Handles: ~50 concurrent users, <100 req/s
- Bottleneck: single SQLite writer serializes writes

### Phase 2: Single node, multi-worker

```
Nginx (1) → Gunicorn (4 workers × Uvicorn) → SQLite (WAL)
```

- Handles: ~200 concurrent users, ~400 req/s reads
- SQLite WAL allows concurrent reads across all workers
- Write serialization still exists; typically not the bottleneck for todo workloads

### Phase 3: Multi-node (database migration trigger)

```
Load Balancer → Nginx (×N) → Backend (×N) → PostgreSQL (primary + read replica)
```

**Trigger:** When sustained write throughput exceeds SQLite WAL queue depth, or when HA/DR requirements mandate multi-node storage.

**Migration cost:** Change `DATABASE_URL` env var. Update `asyncpg` in deps. Run `alembic upgrade head`. **Application code unchanged.**

### Phase 4: Full cloud-native

- CDN for frontend bundle (CloudFront/Cloudflare)
- Auto-scaling backend containers (ECS/EKS)
- Managed PostgreSQL RDS (Multi-AZ)
- Redis for rate limiting (distributed, replaces in-memory slowapi)
- Object storage for future file attachments (S3/R2)

---

## Stateless Backend Design

Every Uvicorn worker is stateless — no in-process session state. This is what enables horizontal scaling:

- No in-memory session store (refresh tokens in DB)
- No in-memory rate limiter in Phase 3 (Redis-backed)
- No in-memory job queue (no periodic jobs except DB purge — handled by cron or a separate container)
- Configuration via environment variables only (12-factor app)

---

## Async-First Architecture

FastAPI + aiosqlite + async SQLAlchemy means:
- I/O-bound operations do not block the event loop
- Each Uvicorn worker handles hundreds of concurrent requests (not just one per OS thread)
- Connection pool is properly managed (SQLAlchemy async engine handles pool lifecycle)

---

## Caching Design Points (Future Extension)

The repository layer exposes a clean interface that allows caching to be inserted as a decorator or middleware:

```
Client → Cache Layer (Redis, in-memory TTL) → Repository → DB
```

Cache invalidation: on any write mutation, invalidate the relevant keys. TanStack Query on the frontend provides additional client-side caching (reduces server round-trips regardless of server-side cache).

---

## Reliability Strategy

### Graceful Shutdown

FastAPI lifespan context manager handles:
1. Stop accepting new connections
2. Wait for in-flight requests to complete (with timeout)
3. Close DB connection pool
4. Exit 0

Uvicorn signal handling: `SIGTERM` triggers graceful shutdown. Nginx `proxy_read_timeout` is set high enough to not cancel in-flight requests during deploys.

### Health Checks

- `/api/v1/health`: liveness (process is alive) — returns 200 always if process running
- `/api/v1/ready`: readiness (DB is reachable) — returns 503 if DB unresponsive

Container orchestrator uses readiness: do not send traffic until DB is ready.

### Failure Isolation

- DB errors do not crash the process — caught at repository layer, mapped to HTTP 503
- Validation errors do not surface stack traces — Pydantic exceptions mapped to 422
- All unhandled exceptions: logged with full traceback (server-side), 500 response (client-side, no details)

---

## Consequences

- All state must be in the database (or passed in the request) — never in process memory
- Periodic jobs (token cleanup, soft-delete purge) are external (cron container or systemd timer)
- Rate limiter is in-process for v1; must migrate to Redis before multi-node Phase 3
