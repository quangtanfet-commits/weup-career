# Thin-slice Spike — Kế hoạch (CHƯA chạy)

> ⛔ **BLOCKED**: chưa có implementation (`backend/app/` chưa tồn tại). Spike cần code thật ở các bề mặt SPI. Tài liệu này là **kế hoạch + time-budget**; chạy khi có khung dự án.

## Mục tiêu (điều spike sẽ falsify hoặc xác nhận)
1. Các SPI load-bearing **compose** được: đăng ký → cổng consent → submit trắc nghiệm (mã hóa+audit) → sinh gợi ý (rationale) → xác nhận.
2. **Độ trễ thực** vs SLO (NFR-01: p99<150ms read/<300ms write) — thay SLO khát vọng bằng baseline đo được.
3. **Plumbing dữ liệu nhạy cảm**: Field Crypto + audit-trong-cùng-giao-dịch hoạt động end-to-end (CP-3 fail-closed).
4. **SQLite→Postgres**: cùng code chạy trên cả hai (ADR-002).

## Lát cắt hẹp nhất (happy path)
`POST /auth/register (<16) → /guardians/invite → /guardians/consent → /assessments/riasec/submit → /recommendations → /recommendations/{id}/confirm`

Stub: nội dung nghề từ file JSON; VNeID = mock; message bus = log-line. **Bề mặt SPI phải thật**: Consent Guard, Field Crypto, Audit Writer, RBAC.

## Tiêu chí thoát
- 1 E2E test chạy hết happy path, assert: account_status chuyển đúng, `assessment_result` mã hóa, **audit count tăng đúng**, recommendation có rationale, confirm bởi người.
- Đo p50/p99 cho submit & recommendation; ghi baseline vào đây.

## Time-budget
**4–6 person-days.** Vượt budget ⇒ dừng, xem lại thiết kế (tín hiệu SPI không compose).

## Kết quả đo (N-1 load test, 2026-06-02)

Đo bằng harness Locust native (`backend/loadtest/`), 200 VU đồng thời, single-node
SQLite, 0 % lỗi trên 50.982 request. Chi tiết + phân tích hotspot:
`docs/performance/n1-load-test-2026-06.md` §10. Run-id `n1-baseline-20260602T114940Z`,
commit `b34ca8c`.

| Metric | SLO | Đo được (single-node SQLite, 200 VU) | Verdict |
|---|---|---|---|
| p99 submit trắc nghiệm | <300ms | **1400ms** (p50 190ms) | ❌ FAIL |
| p99 GET kết quả (giải mã+audit) | <150ms | **1400ms** (p50 170ms) | ❌ FAIL |
| audit completeness end-to-end | 100% | 100% (0 lỗi / 50.982 req) | ✅ PASS |

**Diễn giải:** baseline đo được đã thay thế SLO khát vọng (mục tiêu #2). Đây là
**trần single-node SQLite** chứ không phải lỗi code: serialization 1-writer của
SQLite chi phối độ trễ đuôi ở 200 VU (GET kết quả cũng ghi audit append-only
trong txn đọc — CP-3). p50 lành mạnh (170–240ms); hệ thống nhanh khi không tranh
chấp, chỉ vỡ ở đuôi khi đồng thời cao. NFR-01 cần đo lại trên Postgres +
connection pooling (ADR-002). Gate C **chưa** tick — diện ngoại lệ đã được owner
duyệt (2026-06-02); đo lại trên Postgres theo dõi tại
[#73](https://github.com/quangtanfet-commits/weup-career/issues/73). Gate C chỉ
tick khi lần đo lại đó đạt SLO (xem §10.3).
