# Chiến lược Khả năng Mở rộng & Độ tin cậy — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Thay thế:** v1.0.0 (scalability Todo app)

> Quy mô mục tiêu: nền tảng hướng nghiệp **quốc gia** (B2B2C trường học). MVP single-node SQLite → PostgreSQL + multi-node khi mở rộng cấp Sở/toàn quốc. Lưu ý ràng buộc **dữ liệu nhạy cảm** (không cache thô) và **audit append-only**.

---

## Mục tiêu độ tin cậy
| Tiêu chí | Mục tiêu |
|---|---|
| Uptime/tháng | 99.9% (≤43 phút) |
| p50 read | <30ms |
| p99 read | <150ms |
| p99 write | <300ms |
| 5xx rate | <0.1% |
| Thời gian phục hồi sau crash | <30s |

---

## Failure modes & cô lập

### DB không sẵn sàng
- Repository bắt `OperationalError` → HTTP 503 `SERVICE_UNAVAILABLE`; không lộ trace.
- `/api/v1/ready` trả 503 → orchestrator ngừng route traffic.

### Worker crash
- Gunicorn + Uvicorn workers; worker chết respawn <5s; worker khác vẫn phục vụ.
- Dev: single Uvicorn + Docker `restart: unless-stopped`.

### Áp lực bộ nhớ
- Pool `pool_size=5, max_overflow=10`; body limit 1MB; pagination mặc định 50, tối đa 100.
- Container memory limit (cấu hình Compose).

### ⭐ Lỗi liên quan dữ liệu nhạy cảm / audit
- **Audit store append-only**: nếu ghi audit thất bại khi đọc dữ liệu nhạy cảm → **fail-closed** (từ chối đọc) để giữ CP-3, không phục vụ dữ liệu mà không audit.
- Khóa `FIELD_ENCRYPTION_KEY` lưu qua secret; mất khóa = mất khả năng giải mã ⇒ backup khóa theo quy trình riêng (xem runbook).

---

## Graceful Shutdown
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect(); logger.info("event", event="startup.complete")
    yield
    logger.info("event", event="shutdown.begin")
    await database.disconnect(); logger.info("event", event="shutdown.complete")
```
Nginx `proxy_read_timeout 300s`; Compose `stop_grace_period: 30s` cho request đang xử lý hoàn tất trước SIGKILL (NFR-18, CP không bị vi phạm giữa chừng).

---

## Lớp trừu tượng CSDL (Ports & Adapters)

### Port interface (ví dụ Assessment)
```python
class IAssessmentRepository(Protocol):
    async def save_result(self, user_id: UUID, instrument_id: UUID, payload: bytes) -> AssessmentResult: ...
    async def get_result(self, result_id: UUID, owner_id: UUID) -> AssessmentResult | None: ...
    async def list_results(self, user_id: UUID) -> list[AssessmentResult]: ...
    async def delete_result(self, result_id: UUID, owner_id: UUID) -> bool: ...
```
Các Port khác: `IUserRepo`, `IConsentRepo`, `ICompetencyRepo`, `ICareerRepo`, `IRecoRepo`, `IAuditRepo`.

### Adapter hiện tại: SQLite qua SQLAlchemy
```python
class SQLAlchemyAssessmentRepository:
    async def get_result(self, result_id, owner_id):
        row = (await self._session.execute(
            select(AssessmentResultModel)
            .where(AssessmentResultModel.id == result_id)
            .where(AssessmentResultModel.user_id == owner_id))).scalar_one_or_none()
        return AssessmentResult.from_orm(row) if row else None
```

### Adapter tương lai: PostgreSQL (không đổi code app)
1. `pip install asyncpg`
2. `DATABASE_URL=postgresql+asyncpg://user:pass@host/db`
3. `alembic upgrade head`
4. Deploy — code ứng dụng giữ nguyên.

> Ở quy mô quốc gia, **PostgreSQL là mặc định production** (đồng thời cần cho mã hóa/audit/phân tích quy mô lớn). SQLite chỉ cho MVP/dev.

---

## Thiết kế caching

### MVP: không cache server-side
SQLite WAL đủ nhanh ở quy mô MVP. TanStack Query cache phía client (staleTime 30s) cho dữ liệu **không nhạy cảm**.

> ⛔ **Không cache kết quả trắc nghiệm/gợi ý cá nhân** (dữ liệu nhạy cảm) — không lưu lâu ở client, không đưa vào cache dùng chung. Mỗi lần đọc phải qua audit (CP-3).

### Giai đoạn sau: cache server-side (Redis) cho dữ liệu CÔNG KHAI
```
Request → Redis (TTL) → PostgreSQL   (chỉ cho dữ liệu không nhạy cảm)
```
Cache keys an toàn để cache:
- `career:list:{filter_hash}` → thư viện nghề (đổi hiếm)
- `career:single:{id}`, `content:{dieu5}:{phase}:{level}` → nội dung nghề/bài học
- `competency:tree` → cây 12 năng lực (gần như tĩnh)

**Không cache:** `assessment_result:*`, `recommendation:*`, hồ sơ cá nhân trẻ — dữ liệu nhạy cảm.

Decorator caching áp cho repo dữ liệu công khai:
```python
class CachingCareerRepository:
    async def list(self, filters):
        key = f"career:list:{hash(filters)}"
        if (c := await self._cache.get(key)): return deserialize(c)
        res = await self._inner.list(filters)
        await self._cache.setex(key, 300, serialize(res)); return res
```

---

## Điểm mở rộng async/event-driven
```python
class AssessmentService:
    async def submit(self, ...) -> AssessmentResult:
        result = await self.repo.save_result(...)
        await self.event_bus.publish(AssessmentSubmitted(user_id=..., instrument="riasec"))
        return result
```
Event bus tiêm qua DI: `InMemoryEventBus` (MVP/test) → `RedisEventBus` (mở rộng) → `KafkaEventBus` (quy mô lớn, vd đồng bộ CSDL quốc gia GD&ĐT).
> Sự kiện **không mang nội dung nhạy cảm** trong payload (chỉ id/loại) để tránh rò rỉ qua hạ tầng message.

---

## Retry Strategy
```python
@retry(retry=retry_if_exception_type(OperationalError),
       wait=wait_exponential(multiplier=0.1, max=1), stop=stop_after_attempt(3))
async def execute_with_retry(session, query): return await session.execute(query)
```
Chỉ retry lỗi tạm thời (lock/timeout). **Không** retry: constraint violation, auth/consent failures, lỗi ghi audit (fail-closed).

Frontend: TanStack Query mutation `retry: 1`; Axios interceptor auto-retry sau refresh 401; không retry 4xx nghiệp vụ.

---

## Backup & Recovery
| Thành phần | Chiến lược | RPO | RTO |
|---|---|---|---|
| DB (SQLite→Postgres) | Daily backup + weekly off-site; Postgres: WAL archiving/PITR | 24h→gần 0 | 30min |
| **Audit store** | Backup riêng, **append-only/immutable**; không sửa/xóa | gần 0 | 30min |
| **FIELD_ENCRYPTION_KEY** | Lưu trữ an toàn riêng (HSM/secret manager); versioned theo key id | 0 | 10min |
| Docker images | GHCR (immutable) | 0 | 5min |
| Secrets/Config | Secret manager / git | 0 | 5–10min |

> ⚠️ Phục hồi DB nhưng **mất `FIELD_ENCRYPTION_KEY`** = không giải mã được kết quả nhạy cảm. Khóa và DB phải có chiến lược backup **độc lập nhưng đồng bộ phiên bản**. Quy trình chi tiết: [`docs/operations/runbook.md`](../operations/runbook.md).

---

## Lộ trình mở rộng theo segment người dùng
| Giai đoạn | Người dùng | Hạ tầng |
|---|---|---|
| MVP | THCS + THPT (1 trường/cụm thí điểm) | Single-node SQLite |
| 2 | + Tiểu học; nhiều trường | Multi-worker; PostgreSQL |
| 3 | + người đi làm; cấp Sở/quốc gia | LB → API (×N) → Postgres (primary+replica) → Redis (cache công khai); adapter CSDL quốc gia GD&ĐT |
