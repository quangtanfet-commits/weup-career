# ADR-002: Database Selection and Abstraction Strategy

**Status:** Accepted  
**Date:** 2026-05-27  
**Deciders:** Engineering Team  

---

## Context

We need persistent storage cho user accounts, guardian consent, kết quả trắc nghiệm (nhạy cảm, mã hóa), cây năng lực & tiến bộ, thư viện nghề, gợi ý, audit log. Triển khai ban đầu là single-node Docker Compose. Lựa chọn phải:

1. Chạy với zero external dependency cho MVP (tự chứa)
2. Cho phép migrate sang RDBMS mạng **không phải viết lại code** (PostgreSQL ở production cấp Sở/quốc gia)
3. Đọc đồng thời từ nhiều worker
4. ACID đầy đủ
5. Hỗ trợ **mã hóa trường nhạy cảm** (kết quả trắc nghiệm) và **audit log append-only**

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

Cho MVP single-node (cụm trường thí điểm THCS/THPT), SQLite là lựa chọn đúng. **Ở quy mô cấp Sở/quốc gia, production chuyển sang PostgreSQL** (xem `docs/scalability/strategy.md`) — cần cho JSONB/GIN (lọc `riasec_codes`), replica, và phân tích quy mô lớn.

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
| MongoDB | Breaks ACID for relational data (user ↔ consent ↔ assessment ↔ competency ↔ recommendation); impedance mismatch |
| PlanetScale / Turso | Introduces external cloud dependency; vendor lock-in; unnecessary for v1 |
| In-memory only | Survives restarts — unacceptable |

---

## Consequences

### Constraints accepted
- Single writer at a time (SQLite WAL limitation) — acceptable given expected write volume
- No stored procedures (SQLite limitation) — no business logic in DB; all in service layer (preferred)
- No JSON column indexing ở SQLite — lọc `riasec_codes` ở MVP dùng cách đơn giản; **JSONB/GIN khi lên PostgreSQL** (một lý do chuyển sớm ở production)
- SQLite file phải nằm trên persistent volume; không dùng ephemeral storage
- **Trường nhạy cảm (`assessment_result.result_payload`) mã hóa ở tầng ứng dụng (Field Crypto)** trước khi ghi — không phụ thuộc DB; **audit log append-only** (CP-3)

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
