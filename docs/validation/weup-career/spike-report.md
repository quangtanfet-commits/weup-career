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

## Kết quả đo (điền sau khi chạy)
| Metric | SLO | Đo được |
|---|---|---|
| p99 submit trắc nghiệm | <300ms | _TBD_ |
| p99 GET kết quả (giải mã+audit) | <150ms | _TBD_ |
| audit completeness end-to-end | 100% | _TBD_ |
