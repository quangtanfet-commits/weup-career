# Coverage gate cho các lớp tới hạn (NFR-19) — N-2

**Phiên bản:** 1.0.0 | **Ngày:** 2026-06-02
**Liên quan:** [spec.md NFR-19](../spec.md), [testing/strategy.md](./strategy.md) (§Coverage Configuration, §CI Quality Gate Summary), CP-1…CP-6
**Trạng thái:** đo lường xong → bổ sung enforcement gate (PR N-2)

> NFR-19 yêu cầu **≥95% toàn cục** và **100% line+branch** trên 4 lớp pháp lý/nhạy cảm: **auth · consent · sensitive-data · recommendation**. Tài liệu này (a) ghi nhận bằng chứng 4 lớp **đã đạt 100%**, và (b) đặc tả **gate CI bắt buộc** để 100% đó không thể âm thầm tụt lại — biến NFR-19 từ *mục tiêu* thành *điều kiện chặn merge*.

---

## 1. Vấn đề: 100% không được enforce

CI hiện chỉ chạy một cổng coverage **toàn cục**:

```
pytest tests/ --cov=app --cov-fail-under=95
```

`--cov-fail-under=95` tính trên **toàn bộ `app`**. Một module tới hạn (ví dụ `app/auth/service.py`) có thể tụt từ 100% xuống 95% mà CI **vẫn xanh**, miễn là trung bình toàn cục ≥ 95%. Tức là dòng "100% trên consent/sensitive/auth/reco" trong [strategy.md](./strategy.md) là **kỷ luật thủ công**, không có răng. N-2 lắp răng cho nó.

---

## 2. Bằng chứng: 4 lớp đã ở 100% (đo 2026-06-02)

Chạy đủ bộ test (436 tests) với coverage giới hạn vào đúng các module tới hạn:

| Lớp | Module | Cover (line/branch) |
|---|---|---|
| **auth** | `app/auth/*` (age, models, repository, router, schemas, service) + `app/core/security.py` | 100% / 100% |
| **consent** | `app/guardians/*` + `app/core/consent.py` | 100% / 100% |
| **sensitive** | `app/assessments/*` + `app/core/crypto.py` + `app/core/audit.py` | 100% / 100% |
| **reco** | `app/reco/*` (engine, service, repository, router, schemas, models) | 100% / 100% |
| **authz/ratelimit** | `app/core/authz.py` (RBAC quan hệ) + `app/core/ratelimit.py` (chống brute-force auth, PT-03/05) | 100% / 100% |

`TOTAL: 1210 stmts / 0 miss · 182 branch / 0 partial = 100%`.

### 2.1 100% là **có ý nghĩa**, không bị gaming

Toàn bộ exclusion là `pragma: no cover` chính đáng (không có `...` stub che logic):

| File | Dòng | Lý do loại trừ |
|---|---|---|
| `app/assessments/seed.py` | `async def _run()`, `if __name__ == "__main__"` | CLI entry point (seed script), không phải app logic |
| `app/assessments/scoring.py` | `if scorer is None` | Nhánh phòng thủ — đã được enum chặn ở mọi call site |
| `app/reco/engine.py` | `if cand is None` | Nhánh phòng thủ — top ids luôn đến từ candidates |

Coverage đạt 100% bằng assertion hành vi thật (xem [strategy.md §Backend Testing](./strategy.md) — test đặt tên theo CP-1…CP-6, không mock DB ở integration).

---

## 3. Phạm vi gate (include set)

Gate chạy `coverage report` giới hạn vào đúng tập module sau, yêu cầu **`--fail-under=100`**:

```
app/auth/*
app/guardians/*
app/assessments/*
app/reco/*
app/core/consent.py
app/core/crypto.py
app/core/security.py
app/core/audit.py
app/core/authz.py
app/core/ratelimit.py
```

**Quyết định phạm vi:**
- **Dùng glob thư mục** (`app/auth/*`, …) thay vì liệt kê từng file → mọi **file mới** thêm vào lớp tới hạn **tự động bị gate 100%**. Cơ chế này hoạt động vì run chính dùng `--cov=app` (source=`app`), nên coverage báo cáo cả file chưa từng import dưới `app` là 0% → file tới hạn mới mà thiếu test sẽ **fail ngay**.
- **Bao gồm cả `authz` + `ratelimit`**: authz = enforcement RBAC quan hệ (lõi của consent/auth); ratelimit = phòng thủ brute-force endpoint auth (khắc phục PT-03/PT-05). Cả hai là security-critical và đang ở 100% → gate khóa mức đó lại.
- Tập này là **superset** của danh sách "100% branch bắt buộc" ở [strategy.md dòng ~276](./strategy.md) (vốn chỉ nêu các `service.py` + core): gate mới siết toàn package (kể cả router/repository/schemas/models) — không tốn gì vì tất cả đã 100%.

---

## 4. Cơ chế enforcement (không chạy test 2 lần)

Gate **tái dùng** file dữ liệu `.coverage` do bước test chính sinh ra — **không** chạy lại 436 test, gần như không tốn thêm thời gian CI:

```bash
# Bước 1 (đã có): test chính ghi .coverage
pytest tests/ --cov=app --cov-report=xml --cov-report=term-missing --cov-fail-under=95

# Bước 2 (mới): report giới hạn vào lớp tới hạn, yêu cầu 100%
coverage report \
  --include="app/auth/*,app/guardians/*,app/assessments/*,app/reco/*,app/core/consent.py,app/core/crypto.py,app/core/security.py,app/core/audit.py,app/core/authz.py,app/core/ratelimit.py" \
  --fail-under=100
```

**Tại sao aggregate-100% ⟺ per-file 100%:** `--fail-under=100` áp lên *tổng* của tập include. Tổng = 100% chỉ khi **mọi dòng + mọi nhánh** trong tập đều được phủ — một dòng hở duy nhất kéo tổng < 100% → exit non-zero → fail CI. Vì vậy không cần (và coverage.py không có sẵn) cổng per-file riêng lẻ.

`branch = true` đã bật toàn cục trong `[tool.coverage.run]`, nên report giới hạn này tự động tính cả branch.

---

## 5. Quan hệ với cổng toàn cục

- Cổng **toàn cục** `--cov-fail-under=95` **giữ nguyên** — gate mới **bổ sung**, không thay thế, không nới lỏng bất kỳ ngưỡng nào.
- Hai cổng độc lập: toàn cục bắt mức trung bình toàn app; gate tới hạn bắt từng lớp pháp lý/nhạy cảm phải tuyệt đối.

---

## 6. Bảo trì

- **Thêm file vào lớp tới hạn** (ví dụ `app/auth/new_module.py`): tự động bị gate (glob). Phải có test phủ 100% trước khi merge.
- **Thêm một lớp tới hạn mới** (ví dụ một domain nhạy cảm mới): cập nhật include set ở cả CI step và mục §3 ở đây.
- **`pragma: no cover` mới**: chỉ cho CLI entry point hoặc nhánh phòng thủ thực sự bất khả đạt; mỗi pragma phải có comment lý do (xem §2.1). Reviewer chặn nếu pragma dùng để né test logic thật.
