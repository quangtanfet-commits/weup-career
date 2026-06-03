# Best Practices — WeUp Career

Cách làm **đã chứng minh hiệu quả** ở repo này. Khác với engineering-rules
(luật cứng), đây là khuôn mẫu nên theo.

## Cắt lát dọc (vertical slicing)

- BE phase1→8 và FE F1→8 mỗi lát là một increment chạy được + test + PR riêng.
  Giữ mô hình này: dễ review, dễ rollback, dễ chạy song song.
- Lát đầu tiên luôn là **legal core** (auth + consent) vì mọi thứ phụ thuộc nó.

## Doc-first thực chất

- Mỗi task có doc trước: spec / ADR / ops-doc. Ví dụ mẫu tốt:
  `docs/ops/backend-https-443.md`, `docs/testing/e2e-native-mailer-outbox.md`.
- Doc nêu **Problem → Decision → Details → Non-goals → Verification**.

## Formal verification đi cùng code

- Mỗi họ TLA+ có **base + MC + Sab**. Luôn viết biến thể sabotage để chứng minh
  invariant đủ mạnh (phá impl predicate → TLC phải đỏ).
- Spec phản ánh hành vi impl THẬT (không trừu tượng hoá mất error path / [CRED_A77A1A1F]).

## Backend hexagonal

- Service thuần logic, không import FastAPI. Repository = Protocol port +
  adapter SQLAlchemy. Test service không cần web layer.
- Token: hash-only at rest (RefreshToken, EmailVerificationToken) — chỉ lưu
  SHA-256, raw chỉ đi trong link/response.

## Frontend

- **Public RSC page fetch dữ liệu backend phải `force-dynamic`** — nếu không
  Next build (lúc không có backend) sẽ bake danh sách rỗng → E2E locator rỗng.
- **Chạy Prettier trước khi tuyên bố xong** — CI chạy `format:check` riêng,
  `npm run lint` KHÔNG bao gồm.
- Major bump (Next/Tailwind/Vitest) cô lập từng lát; chú ý coupling
  next-intl ↔ eslint.
- RoleGate đọc role từ token claim; backend vẫn là thẩm quyền cuối.

## E2E native (do ràng buộc DinD)

- Chạy prod build trên **:3100 same-origin** qua Next rewrite gated
  `E2E_PROXY_API=1`; KHÔNG cross-origin tới backend (CORS dev-only chặn).
- Harness **tự sở hữu backend ephemeral** cho e2e: boot `:8000` với
  `WEUP_MAILER_OUTBOX` run-scoped, copy seed DB → `report/<run>/e2e/app.db` rồi
  `alembic upgrade head`, tắt rate-limit (config test), teardown qua `setsid` +
  `kill -- -$PGID`.

## CI/CD

- Dependabot bật; pin action theo SHA; gate Trivy/Semgrep/ZAP fail-closed.
- Mỗi PR đính report HTML (suites + coverage + security + TLA+ + perf + trend).

## Vận hành dev (codify, đừng để "bay hơi")

- Bind `:80`/`:443` không cần root (sysctl=0). Khi cần trải nghiệm thử, **viết
  script** (`scripts/dev-up.sh`) thay vì lệnh thủ công — để tái lập qua restart.
- Tạo user demo bằng script có thể xoá sạch; mật khẩu demo chỉ dùng cho dev.
