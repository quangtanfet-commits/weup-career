# ADR-002: Database Selection and Abstraction Strategy

**Status:** Accepted  
**Date:** 2026-05-27  
**Deciders:** Engineering Team  

---

## Context

We need persistent storage for user accounts, todos, tags, and session tokens. The initial deployment is a single-node Docker Compose setup. The choice must:

1. Work with zero external service dependencies (fully self-contained)
2. Allow future migration to a networked RDBMS without application-code rewrites
3. Handle concurrent reads from multiple Uvicorn/Gunicorn workers
4. Support full ACID transactions

---

## Decision

**Use SQLite 3.45 (WAL mode) with aiosqlite for async I/O, accessed exclusively through SQLAlchemy 2.0 async ORM.**

---

## Rationale

### Why SQLite is appropriate for v1

SQLite is not "toy" storage. It is:
- The most deployed database engine in the world (embedded in billions of devices)
- Fully ACID compliant with WAL mode
- Capable of 100k+ reads/sec on modern hardware
- A single file — trivial backup (`cp app.db backup.db`)
- Zero operational overhead — no separate process, no networking, no config

For a single-node Todo application with <10,000 users, SQLite is not a constraint — it is a correct choice.

**WAL mode specifics:**
- Write-Ahead Logging enables concurrent reads without blocking writes
- Multiple readers (Gunicorn workers) can read simultaneously
- One writer at a time — acceptable for our write throughput
- WAL file auto-checkpointed; no manual management needed

### Why the abstraction matters (future migration path)

The application accesses the database **only through SQLAlchemy**. No raw SQL strings in application code. No sqlite3 module calls outside of SQLAlchemy internals.

**Migration to PostgreSQL requires only:**
1. Change `DATABASE_URL=postgresql+asyncpg://...`  
2. Add `asyncpg` to dependencies  
3. Run `alembic upgrade head` on new DB

**Zero application code changes.** This is the critical design constraint.

---

## Alternatives Considered

| Database | Verdict |
|----------|---------|
| PostgreSQL | Correct long-term choice; adds operational complexity for v1 (container, config, password management, connection pooling). Defer to Phase 3 migration. |
| MySQL / MariaDB | Less precise type system; less clean JSON support; no meaningful advantage over PostgreSQL |
| MongoDB | Breaks ACID for relational data (todos with tags, users, tokens); impedance mismatch |
| PlanetScale / Turso | Introduces external cloud dependency; vendor lock-in; unnecessary for v1 |
| In-memory only | Survives restarts — unacceptable |

---

## Consequences

### Constraints accepted
- Single writer at a time (SQLite WAL limitation) — acceptable given expected write volume
- No stored procedures (SQLite limitation) — no business logic in DB; all in service layer (preferred)
- No JSON column indexing (SQLite limitation) — no JSONB columns in schema
- SQLite file must be on a persistent volume in Docker; not ephemeral storage

### Design rules enforced by this decision
- All DB access goes through the SQLAlchemy async session
- Repository classes depend only on `AsyncSession`, not on any SQLite-specific API
- All schema changes go through Alembic migrations — no `CREATE TABLE IF NOT EXISTS` in application startup
- `engine_kwargs` are environment-specific (WAL pragma applied at connection level)
- Pool size: `check_same_thread=False` (SQLite) automatically set by SQLAlchemy async driver

### Alembic Migration Strategy
- One migration file per schema change (atomic)
- Migrations are always reviewed before merge
- `alembic downgrade -1` must always work (reversibility enforced)
- Seeding data done via a separate `seed.py` script, not migrations
