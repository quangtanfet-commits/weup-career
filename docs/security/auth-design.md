# Thiết kế Xác thực & Phân quyền — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Thay thế:** v1.0.0 (auth Todo app)

> Phân quyền của WeUp Career có **ba lớp**: (1) xác thực (JWT), (2) **cổng đồng ý giám hộ** cho dữ liệu trẻ <16, (3) **RBAC quan hệ** (guardian↔child, counselor↔student theo trường). Neo vào [`docs/spec.md`](../spec.md) §8 (CP-1, CP-4, CP-7) và [`docs/legal/legal-basis.md`](../legal/legal-basis.md) §6.

---

## Kiến trúc xác thực

### Tổng quan vòng đời token
```
Register/Login
     │
     ▼
┌─────────────────┐     ┌──────────────────────────────┐
│  access_token   │     │      refresh_token           │
│  (JWT, 15 phút) │     │  (random, 7 ngày)            │
│  in: memory     │     │  in: httpOnly cookie         │
│  sent: Bearer   │     │  sent: tự động ở /auth/refresh│
└─────────────────┘     └──────────────────────────────┘
        │                         │
        │ hết hạn 15'             │ tự refresh 60s trước khi access hết hạn
        ▼                         ▼
   401 response ──────────► Token Rotation (cũ revoke, mới phát hành — nguyên tử, CP-7)
```

---

## Cấu trúc JWT Claims

### Access Token
```json
{
  "sub": "usr_01HX...",
  "email": "user@example.com",
  "user_type": "student",
  "age_band": "under_16",
  "account_status": "active",
  "roles": ["student"],
  "iat": 1716800000,
  "exp": 1716800900,
  "jti": "tkn_01HX...",
  "sv": 1,
  "iss": "weup-api"
}
```
> `age_band` + `account_status` đưa vào claim để **Consent Guard** quyết nhanh không cần round-trip DB cho mỗi request; nhưng quyết định cuối về consent vẫn xác thực lại với DB ở route xử lý dữ liệu nhạy cảm (claim có thể cũ tối đa 15'). `roles` hỗ trợ RBAC.

---

## Lưu trữ mật khẩu
```
"MyPassword123" → bcrypt.hashpw(pw, gensalt(rounds=12)) → "$2b$12$..." (60 ký tự)
```
Verify: `bcrypt.checkpw(candidate, stored_hash)` — thời gian hằng số. Có thể nâng Argon2id ở giai đoạn sau (passlib migrate-on-login, không phá hash cũ).

---

## Xoay vòng Refresh Token (CP-7)
```
Client                              Server
  │── POST /auth/refresh ───────────►│
  │   Cookie: refresh_token=RT_OLD   │ 1. SHA-256 RT_OLD → lookup
  │                                  │ 2. Verify: chưa revoke, chưa hết hạn
  │                                  │ 3. Cùng 1 transaction (nguyên tử):
  │                                  │    INSERT RT_NEW (active)
  │                                  │    UPDATE RT_OLD revoked_at=NOW()
  │◄─ 200 {access_token: AT_NEW} ────│
  │   Set-Cookie: refresh_token=RT_NEW
```
**Re-use detection:** RT_OLD trình lại sau rotation → đã revoke → 401. Nâng cấp: phát hiện reuse ⇒ revoke **toàn bộ** refresh token của user (nghi ngờ chiếm phiên).

---

## Denylist Access Token khi logout (H-01)

**Trạng thái:** Đã triển khai (2026-06-01). Đóng lỗ hổng pentest PT-01 (hạ HIGH→LOW; xem lại 2026-08-31).

Access JWT là **stateless** nên trước đây vẫn hợp lệ tới `exp` (≤15') kể cả sau khi logout — token bị đánh cắp hoặc dùng lại sau logout vẫn replay được. H-01 đưa `jti` của access token vào **danh sách thu hồi** trong thời gian sống còn lại để chặn replay.

```
Client                                Server
  │── POST /auth/logout (Bearer AT) ──►│ 1. Revoke refresh token (như cũ)
  │                                    │ 2. INSERT revoked_access_token
  │                                    │    (jti, user_id, expires_at = AT.exp)
  │                                    │    + audit auth.access_revoked
  │◄─ 204 No Content ──────────────────│
  │── GET /auth/me (Bearer AT cũ) ────►│ jti nằm trong denylist → 401
```

- **Lưu trữ:** bảng `revoked_access_token` (`jti` unique-index, `user_id` FK CASCADE, `expires_at` = `exp` của token, `created_at`). Migration `b1f2c3d4e5a6`.
- **Kiểm tra khi xác thực:** `get_current_user` / `optional_current_user` từ chối token có `jti` bị denylist → **401**. Điều kiện lọc `expires_at > now`, nên tính đúng đắn **không phụ thuộc** vào việc prune đã chạy hay chưa.
- **Logout chỉ-access:** vẫn thu hồi `jti` ngay cả khi **không có** refresh cookie.
- **Bị chặn theo user:** logout của user A không ảnh hưởng token của user B (cô lập theo `jti`).
- **Bảng có giới hạn:** `add` idempotent (logout 2 lần an toàn) và prune cơ hội các dòng quá `expires_at`, giữ bảng bị chặn bởi TTL access 15' thay vì phình theo mỗi lần logout.
- **Độc lập với formal verification:** H-01 là lớp bổ sung, không đụng vòng đời refresh CP-7 mà TLA+ Gate-B mô hình hóa — không thay đổi `trace_emit`.

> Ngoài phạm vi của H-01 (xem **H-02** bên dưới): vô hiệu hóa **mọi** access token cũ của user khi đăng nhập lại / đổi mật khẩu.

---

## Session-version epoch — vô hiệu hóa hàng loạt access token (H-02)

**Trạng thái:** Đã triển khai (2026-06-01). Dựa trên H-01; đóng lỗ hổng pentest PT-02 (xem lại 2026-08-31).

H-01 chỉ thu hồi **một** token tại đúng lần logout của nó. H-02 vô hiệu hóa **mọi** access token cũ của user **cùng lúc** khi "session epoch" thay đổi — để một access token bị đánh cắp (dạng bare, không kèm refresh cookie) chết ngay khi chủ hợp pháp đăng nhập lại hoặc đổi mật khẩu, không phải chờ hết `exp` của từng token.

```
Client                                  Server
  │── POST /auth/login ─────────────────►│ session_version += 1  (epoch mới)
  │◄─ 200 {access_token: AT (sv=epoch)} ─│ AT đóng dấu sv = epoch hiện tại
  │── GET /auth/me (Bearer AT cũ, sv thấp)►│ sv < session_version → 401
```

- **Cơ chế:** bộ đếm tăng đơn điệu theo user `user.session_version` (mặc định `1`, `server_default '1'`). Migration `c2d3e4f5a6b7`.
- **Đóng dấu trên token:** mỗi access token mang epoch phát hành ở claim `sv` (`create_access_token`); refresh phát lại token ở epoch **hiện tại**.
- **Tăng epoch khi:** (a) **mỗi lần đăng nhập thành công** — nên login mới sẽ "về hưu" các token từ lần login trước; (b) **đổi mật khẩu** (`POST /me/password`), kèm theo **thu hồi toàn bộ refresh-token family** → kill cứng trên mọi thiết bị.
- **Kiểm tra khi xác thực:** `get_current_user` / `optional_current_user` từ chối token có `sv` **thấp hơn** `session_version` sống của user → **401** (`_reject_if_stale_session`).
- **Fall-through (không 401 hàng loạt khi deploy):** **bỏ qua** kiểm tra khi claim `sv` vắng mặt (token cũ trước H-02) hoặc subject không còn tồn tại — giống cơ chế bỏ qua khi thiếu `jti` của H-01. Thiết bị hợp lệ tự khôi phục nhờ refresh cookie phát lại token ở epoch mới.
- **Chi phí:** thêm một lần đọc một-cột (`session_version`) mỗi request đã xác thực; một lần tăng bộ đếm mỗi login / đổi mật khẩu. **Không** sinh dòng mới theo từng token (khác với denylist của H-01).
- **Độc lập với formal verification:** như H-01, là lớp bổ sung — không đụng vòng đời refresh CP-7, không thay đổi `trace_emit`.

> **Vì sao tăng epoch ở mỗi lần login (không chỉ khi đổi mật khẩu)?** Mối đe dọa H-02 nhắm tới là access token bare bị đánh cắp; gắn việc vô hiệu hóa vào ngay lần đăng nhập hợp lệ kế tiếp đóng cửa sổ tấn công mà không cần thao tác từ người dùng. Các phiên hợp lệ song song không bị ảnh hưởng vì chúng giữ refresh cookie và tự phát lại token ở epoch mới.

---

## ⭐ Lớp 2 — Cổng đồng ý giám hộ (Consent Authorization) — CP-1/CP-2

Trước **mọi** route xử lý dữ liệu hướng nghiệp (trắc nghiệm, gợi ý, tiến bộ), một dependency tập trung kiểm tra:

```python
async def require_consent(user = Depends(get_current_user),
                          consents = Depends(get_consent_repo)):
    if user.age_band != "under_16":
        return  # ≥16 tự đồng ý
    active = await consents.has_active(user.id)   # xác thực lại với DB
    if not active:
        raise HTTPException(403, code="GUARDIAN_CONSENT_REQUIRED")
```

- **Đặt ở tầng router** cho tất cả route dữ liệu hướng nghiệp — một điểm duy nhất, không đường vòng (TLA+ `ConsentLifecycle` chứng minh).
- Thu hồi consent ⇒ `has_active` trả false ngay ⇒ dừng xử lý mới (CP-2).
- **Self-consent bị cấm:** trẻ không thể tự đóng vai giám hộ; GuardianLink phải `verified_at` qua kênh độc lập (email/VNeID).

---

## ⭐ Lớp 3 — RBAC quan hệ (CP-4)

Khác v1 (flat RBAC), WeUp Career có nhiều vai trò & quan hệ:

| Vai trò | Được phép | KHÔNG được |
|---|---|---|
| `student` (≥16) | CRUD hồ sơ/kết quả/tiến bộ **của mình**; nhận & xác nhận gợi ý | Dữ liệu người khác |
| `student` (<16) | Như trên **sau khi** có consent active | Xử lý dữ liệu khi chưa consent |
| `guardian` | Đồng ý/thu hồi; **đồng xem** dữ liệu trẻ **được liên kết & verified** | Dữ liệu trẻ khác |
| `counselor` | Xem tiến bộ (đã gỡ nhạy cảm theo quyền) & ghi phiên tư vấn cho **học sinh trong school_id của mình** | Học sinh ngoài trường |
| `school_admin` | Quản lý lớp/HS/counselor trong **school_id** | Dữ liệu cá nhân nhạy cảm chi tiết |
| `working` | CRUD hồ sơ/kết quả/tiến bộ của mình (lớp phi tuyến) | Dữ liệu người khác |

### Thực thi quyền sở hữu & quan hệ (Critical)
```python
def can_access(actor, owner_id) -> bool:
    return (actor.id == owner_id
            or guardian_link_verified(actor.id, owner_id)
            or counselor_of_same_school(actor.id, owner_id))

# Repository LUÔN lọc theo quyền — tầng thực thi cuối
select(AssessmentResult).where(
    AssessmentResult.user_id == owner_id)   # + kiểm tra can_access ở service
```
**Defense in depth:** service kiểm tra quan hệ; repository lọc `user_id`; trả **404** (không 403) khi không sở hữu để tránh xác nhận tồn tại (trừ trường hợp consent → trả 403 `GUARDIAN_CONSENT_REQUIRED` có chủ đích).

---

## ⭐ Kiểm soát truy cập dữ liệu nhạy cảm (CP-3)

- `AssessmentResult.result_payload` mã hóa at-rest qua **Field Crypto** (khóa `FIELD_ENCRYPTION_KEY`, tách khỏi `SECRET_KEY`).
- **Mọi lần đọc** kết quả nhạy cảm đi qua một service duy nhất ghi `audit_log(is_sensitive_access=true)` **trong cùng giao dịch** — không có đường đọc nào bỏ qua audit (TLA+ `SensitiveDataAccess`).
- Không log nội dung; không cache lâu phía client; không index trên nội dung kết quả.

---

## Cấu hình bảo mật phiên

### Nginx Security Headers
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Content-Security-Policy "
  default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';
  img-src 'self' data:; connect-src 'self'; font-src 'self';
  object-src 'none'; frame-ancestors 'none';" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
```

---

## Quản lý bí mật (Secret Management)

### Development
- `SECRET_KEY`, `FIELD_ENCRYPTION_KEY` trong `.env` (gitignored); `.env.example` chỉ tên biến.

### Production
- Docker secret tại `/run/secrets/secret_key` và `/run/secrets/field_encryption_key`; app đọc từ file path.
- **Xoay `FIELD_ENCRYPTION_KEY`** cần chiến lược re-encrypt (versioned key id trên bản ghi) — không xoay tùy tiện vì khóa giải mã dữ liệu nhạy cảm lịch sử.

### Sinh khóa
```bash
openssl rand -hex 32   # 256-bit
```

---

## Audit Logging

Sự kiện auth + **sự kiện pháp lý/nhạy cảm** đều ghi audit (append-only):

```json
{
  "event": "assessment.result.read",
  "actor_id": "usr_01HX...",
  "target_type": "AssessmentResult",
  "is_sensitive_access": true,
  "request_id": "req_01HX..."
}
```

Sự kiện được ghi:
- Auth: `auth.register.*`, `auth.login.*`, `auth.logout`, `auth.access_revoked`, `auth.token.refreshed`, `auth.token.reuse_detected`
- Consent: `guardian.invited`, `guardian.consent.granted`, `guardian.consent.revoked`
- Nhạy cảm (CP-3): `assessment.result.read`, `assessment.result.exported`, `assessment.result.deleted`
- Gợi ý (giải trình AI): `recommendation.created`, `recommendation.confirmed` (kèm `confirmed_by`, `decision`)
- Tài khoản: `user.password_changed`, `user.account_deleted`
