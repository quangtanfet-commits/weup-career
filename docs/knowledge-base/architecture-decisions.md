# Architecture Decisions — WeUp Career

Tóm tắt các quyết định kiến trúc lớn + lý do. ADR đầy đủ ở `docs/adr/`; file
này là chỉ mục có ngữ cảnh để tra nhanh trước khi đụng vùng nhạy cảm.

## Kiến trúc tổng

- **Hexagonal (ports & adapters).** Service thuần logic, không import FastAPI;
  repository là Protocol port + adapter SQLAlchemy. *Vì sao:* test logic không
  cần web layer; dễ thay SQLite→PostgreSQL.
- **SQLite (aiosqlite) cho dev, trừu tượng hoá cho PostgreSQL.** `database_url`
  cấu hình hoá; `migrations/env.py` đọc `get_settings().database_url` nên một
  override redirect cả Alembic lẫn backend.

## Định danh & phiên

- **JWT (ADR-008) stateless + bcrypt (rounds≥12).** Access token mang claim
  `roles` và `sv` (session_version).
- **Roles trong token = `[student|working]` (+ `content_editor` nếu cờ bật).**
  `school_admin`/`counselor` KHÔNG bao giờ phát trong token — chúng là quan hệ
  DB theo trường (`school_membership.role`). *Hệ quả:* tài khoản chỉ có cờ toàn
  cục không thể vào `/school-admin/*` hay `/counselor/*`.
- **H-01 — access-token denylist (`jti`).** JWT stateless không teardown được
  lúc logout ⇒ ghi `jti` tới hạn `exp`; validation từ chối `jti` còn hạn.
- **H-02 — session-version epoch (`sv`).** Bump khi re-login (giết access token
  trộm) và khi đổi mật khẩu (hard session kill + revoke refresh family).
- **N-3 — email verification.** Login gated trên `email_verified_at` non-NULL
  (sau bước credential nên không thành oracle liệt kê). Token hash-only,
  single-use, có `expires_at`. Row cũ backfill `created_at` tránh khoá hàng loạt.
- **PT-04 — chống dò email** (enumeration) ở register/resend.

## Dữ liệu & quyền riêng tư

- **Field-level crypto (ADR-011)** cho dữ liệu cá nhân nhạy cảm (căn cứ BVDLCN).
- **Consent guard (CP-1/CP-2)** cho trẻ <16; **audit (CP-3)**; **authz (CP-4)**;
  **atomic refresh rotation (CP-7)**.

## Formal verification (6 họ TLA+, mỗi họ có base + MC + Sab)

| Spec | Phủ bất biến chính |
|---|---|
| `ConsentLifecycle` | Vòng đời consent: invite/consent/revoke, cấm tự consent |
| `AuthTokenLifecycle` | Phát/refresh/revoke, rotation, denylist, session epoch |
| `AuthorizationModel` | Ranh giới role, school-scope, không rò quyền |
| `SensitiveDataAccess` | Truy cập dữ liệu nhạy cảm theo consent/authz |
| `CompetencyProgress` | Tiến trình năng lực nhất quán, không tụt trạng thái sai |
| `RecommendationGovernance` | Quản trị gợi ý nghề: ràng buộc đầu ra |

*Quy tắc:* sabotage-check mọi invariant lớn; spec tiến hoá cùng code (no
spec-without-code quá 1 wave).

## Topology dev (do DinD)

- Native, không docker compose. FE dev `:3000` (hoặc `:80` ad-hoc); FE prod
  build `:3100`; backend factory `:8000` (+ HTTPS `:443` tuỳ chọn). E2E
  same-origin `:3100` qua Next rewrite gated `E2E_PROXY_API`. Xem
  `docs/ops/backend-https-443.md`.
