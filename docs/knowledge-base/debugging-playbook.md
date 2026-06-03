# Debugging Playbook — WeUp Career

Quy trình gỡ lỗi từng lớp. Mục tiêu: tìm **căn nguyên**, không vá triệu chứng,
không dùng hành động phá huỷ làm lối tắt (vd `--no-verify`).

## 0. Khoanh vùng trước

1. Tái lập được không? Trên CI hay chỉ cục bộ? (flake môi trường vs bug thật —
   xem `lessons-learned` L-11.)
2. Lớp nào: build / [CRED_DE6BACFC] / [CRED_D62FFAB8] / [CRED_27CA9A28] / [CRED_DD2A06EF] / [CRED_9B59B743] / [CRED_9F84CACB]?
3. Có thay đổi gần đây? `git log --oneline -10`, `git diff`.

## 1. Backend không phản hồi

```bash
ss -ltnp | grep -E ':(8000|443)\b'          # có listener không?
curl -sS localhost:8000/api/v1/health -w ' %{http_code}\n'
tail -20 /tmp/weup-backend*.log              # startup/log lỗi
```
- Không listener → relaunch factory; nếu port bị giữ, teardown `kill -- -$PGID`.
- 000 sau idle → dev backend chết lúc idle, relaunch.

## 2. Lỗi auth/login

- 422 → kiểm tra payload (email TLD hợp lệ? password đủ upper+lower+digit?).
- 401 đúng credential → `email_verified_at` NULL (N-3)? `session_version`/`sv`
  lệch (H-02)? `jti` trong denylist (H-01)?
- Không vào được route role → role có trong token claim không? `school_admin`/
  `counselor` cần `school_membership` thật, không phải cờ toàn cục.

## 3. CORS

```bash
curl -ksS -X OPTIONS https://localhost/api/v1/auth/login \
  -H 'Origin: https://localhost' -H 'Access-Control-Request-Method: POST' \
  -D - -o /dev/null | grep -i access-control-allow
```
- Thiếu allow-origin → `CORS_ORIGINS` rỗng (middleware không mount). Set runtime.

## 4. E2E (Playwright native)

- Locator rỗng → RSC prerender tĩnh; thêm `force-dynamic`.
- 429 → rate-limit; backend e2e cần `RATE_LIMIT_ENABLED=false`.
- register 500 → seed DB lệch migration; copy seed + `alembic upgrade head`.
- token verify trượt → kiểm tra `WEUP_MAILER_OUTBOX` reader==writer; outbox
  run-scoped, scan newest-first.
- Bằng chứng: screenshot + video + trace trong `report/<run-id>/`.

## 5. TLA+/TLC

- Counterexample → phân loại: bug thật / [CRED_576C9B36] sai / [CRED_7CC8C53E] quá mạnh
  (dùng `inv_checking_tool` get_tlc_summary/state, compare_tlc_states).
- TLC pass nhưng nghi spec yếu → chạy biến thể `*Sab`: phá impl predicate, TLC
  PHẢI đỏ. Nếu vẫn xanh → invariant quá yếu.
- Trace không khớp impl → `tracedebugger` run_trace_validation → nếu fail,
  run_trace_debugging với breakpoint.

## 6. CI đỏ

- Đọc job fail cụ thể; tái lập lệnh đó cục bộ (cùng version tool — Ruff 0.15,
  mypy, v.v.).
- Security gate (Trivy/Semgrep/ZAP) → vá nguyên nhân, KHÔNG nới gate.
- Format → `npm run format`. Type → `uv run mypy app`. Lint → `ruff check`.

## Nguyên tắc

- Điều tra trạng thái lạ (lock file, branch/file lạ) **trước khi** xoá/đè — có
  thể là việc đang dở của người dùng.
- Sửa căn nguyên, không bypass safety check.
- Mỗi bug đã xác nhận → thêm **regression test** ghim lại (ER); bug do TLC bắt →
  vừa sửa code vừa thêm test replay counterexample.
