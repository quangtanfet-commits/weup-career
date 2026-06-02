# Email verification — closing the PT-04 residual (N-3)

> Status: spec / proposed 2026-06-02 · Scope: `backend/app/auth/*`, new `app/core/mailer.py`, one Alembic migration, `frontend/features/auth/*`
> Related: [docs/security/email-enumeration.md](./email-enumeration.md) (H-04), [ADR-008 Security Controls](../adr/ADR-008-security-controls.md), [ADR-009 Hexagonal](../adr/ADR-009-hexagonal.md), [auth-design.md](./auth-design.md), PT-04 (email enumeration)
> Backlog: N-3 (sau N-2 coverage gate, N-5 PyJWT, N-6 SHA-pin)

## 1. Vì sao N-3 — H-04 đã đóng oracle HTTP, nhưng còn dư

`PT-04` là lỗ **email enumeration** qua `POST /auth/register`. H-04 (Option C,
xem [email-enumeration.md](./email-enumeration.md)) đã đóng oracle `201-vs-409`:
đăng ký trùng email giờ trả về **201 + `UserOut` tổng hợp không phân biệt được**
với đăng ký mới (cùng shape, cùng chi phí bcrypt để cân bằng timing, audit chỉ
phía phòng thủ). Đó là bản vá *triệu chứng*.

Phần **dư** mà N-3 đóng nốt — và là lý do email-enumeration.md §5 kết luận
"bản sửa hoàn chỉnh = email verification":

1. **Chưa hề chứng minh quyền sở hữu email.** Hiện `register` tạo ngay tài khoản
   *dùng được* và FE auto-login. Bất kỳ ai cũng đăng ký được `victim@truong.edu.vn`
   — một email họ không kiểm soát — rồi vận hành tài khoản gắn email đó.
2. **H-04 tạo ra lockout do chính cơ chế suppression.** Vì đăng ký trùng là
   no-op im lặng (201 tổng hợp, không ghi DB), một khi attacker "chiếm chỗ" một
   email, **chủ thật** đăng ký lại sẽ bị nuốt lặng lẽ và **không bao giờ tạo
   được tài khoản** — không có tín hiệu lỗi nào. Đây là tác dụng phụ trực tiếp
   của H-04 mà chỉ email verification mới gỡ được: tài khoản "chiếm chỗ" chưa
   verify sẽ không kích hoạt và hết hạn, trả email về cho chủ thật.
3. **Còn kênh phụ "đăng nhập được hay không".** Khi tài khoản dùng được ngay sau
   register, vẫn còn các oracle tinh vi phía sau. Khi không phiên nào được cấp
   trước lúc chứng minh sở hữu, bề mặt đó biến mất.

→ N-3: **chứng minh quyền sở hữu email trước khi tài khoản dùng được**, đồng thời
**giữ nguyên** tính bất khả phân biệt của `register` mà H-04 đã thiết lập (không
được tái mở oracle).

## 2. Hợp đồng hành vi — thay đổi & bất biến PHẢI giữ

### 2.1 Thay đổi đối ngoại (breaking — có blast radius)

| Bề mặt | Trước | Sau (N-3) |
|---|---|---|
| `POST /auth/register` | `201` + `UserOut` | **`202 Accepted`** + body chung chung (không `UserOut`, không phiên). Vẫn **luôn 202** cho email mới / trùng / hợp lệ → không oracle. |
| Cấp phiên lúc register | Có (FE auto-login) | **Không.** Phiên chỉ cấp sau khi verify + login. |
| `POST /auth/verify-email` | — | **MỚI.** Body `{token}`. Hợp lệ & chưa dùng & chưa hết hạn → set `email_verified_at`, `204`. Sai/hết hạn/đã dùng → lỗi **chung chung** (không enumeration). Idempotent-an toàn (token single-use). |
| `POST /auth/resend-verification` | — | **MỚI.** Body `{email}`. **Luôn `202`** chung chung (không tiết lộ email tồn tại / đã verify). Rate-limited. |
| `POST /auth/login` | verify pw → phiên | Thêm chốt: pw đúng **nhưng** `email_verified_at IS NULL` → `403 email_not_verified`. Pw sai vẫn `401` chung. |

### 2.2 Bất biến PHẢI giữ (test khoá lại)

- **PT-04 / H-04 còn nguyên:** `register` bất khả phân biệt giữa email mới và
  email trùng — cùng status (`202`), cùng body, cùng chi phí bcrypt
  (`verify_password(payload.password, _DUMMY_HASH)` vẫn chạy ở nhánh trùng để cân
  bằng timing). Audit `auth.register.duplicate_suppressed` vẫn chỉ phía phòng thủ.
- **Không enumeration trên bề mặt mới:** `verify-email` và `resend-verification`
  KHÔNG được tiết lộ email có tồn tại / đã verify hay chưa (xem §5).
- **`403 email_not_verified` chỉ sau khi pw đúng** — đây không phải pre-auth
  oracle: caller đã chứng minh biết mật khẩu, nên việc báo "chưa verify" là chuẩn
  ngành (GitHub/Google đều vậy) và mở được luồng resend. Pw sai → `401` chung,
  không đổi.
- **Guardian-consent trực giao với email-verify** (xem §3): under-16 cần CẢ hai
  (email verified **và** consent); adult chỉ cần email verified. Thứ tự độc lập.
- **Refresh-rotation / logout / session-version (CP-7, H-01, H-02)** không đổi.

## 3. Mô hình dữ liệu — flag trực giao, KHÔNG thêm AccountStatus

`email_verified` là một chiều **trực giao** với vòng đời tài khoản. Codebase đã
tách `is_deleted` (cờ boolean) khỏi `account_status` (vòng đời) — ta theo đúng
khuôn đó thay vì nhồi một giá trị enum mới:

- **`account_status`** vẫn là chiều consent/vòng đời: `ACTIVE` /
  `PENDING_GUARDIAN_CONSENT` / `SUSPENDED` / `DELETED`. **Không thêm trạng thái.**
- **`User.email_verified_at: datetime | None`** (cột MỚI) là chốt chứng minh sở
  hữu email. `NULL` = chưa verify.

Lý do không dùng `PENDING_EMAIL_VERIFICATION` enum: một enum đơn không biểu diễn
được tổ hợp trực giao "đã verify email NHƯNG đang chờ consent" vs "chưa verify".
Hai cờ độc lập compose sạch:

| age_band | điều kiện để `login` cấp phiên | điều kiện xử lý dữ liệu nhạy cảm |
|---|---|---|
| adult / 16-17 | `email_verified_at` không NULL | (như hiện tại) |
| under-16 | `email_verified_at` không NULL | + `account_status == ACTIVE` (consent, CP-2) |

### 3.1 Bảng token MỚI — `EmailVerificationToken` (hash-only, single-use)

Theo đúng khuôn `RefreshToken`/`RevokedAccessToken`: **chỉ lưu hash**, raw chỉ ra
ngoài qua email.

```
email_verification_token
  id            UUID  PK
  user_id       FK user.id  ON DELETE CASCADE, indexed
  token_hash    String(64)  unique, indexed   # sha256(raw), giống hash_refresh_token
  expires_at    DateTime(tz)                   # created_at + verification_token_ttl_hours
  consumed_at   DateTime(tz) | NULL            # single-use: set khi verify thành công
  created_at    DateTime(tz)
```

- Raw token = `secrets.token_urlsafe(32)`; chỉ hash đi vào DB (tái dùng
  `hash_refresh_token`/sha256 hiện có).
- Single-use: verify thành công set `consumed_at`; token đã `consumed_at` hoặc
  quá `expires_at` → coi như không hợp lệ (lỗi chung chung).
- Resend phát hành token mới; token cũ chưa dùng của user đó **bị vô hiệu**
  (revoke-all kiểu refresh family) để không tồn đọng nhiều link sống.

### 3.2 Alembic migration — `<rev>_n03_email_verification`

- `down_revision = 'c2d3e4f5a6b7'` (head hiện tại = h02; xác nhận lại bằng
  `uv run alembic heads` trước khi sinh).
- `op.add_column("user", email_verified_at nullable=True)`.
- `op.create_table("email_verification_token", ...)` + index unique `token_hash`,
  index `user_id`.
- **Backfill bắt buộc (nếu không sẽ khoá hết user cũ):** mọi `user` đang tồn tại
  set `email_verified_at = created_at` (coi như đã verify). **Chỉ tài khoản ĐĂNG
  KÝ MỚI** sau migration mới đi qua luồng verify. Ghi rõ trong `upgrade()`.
- `downgrade()`: drop table + drop column.

## 4. Mailer port (hexagonal, ADR-009) — không có SMTP nên dùng adapter

Repo **chưa có** hạ tầng SMTP/mailer (grep `smtp|mailer|send_email` = rỗng), và
devcontainer aarch64/linuxkit **không chạy docker compose** → không dựng được
SMTP thật. Theo ADR-009 (ports + adapters), ta định nghĩa **port** và **adapter**:

```
app/core/mailer.py
  class IMailer(Protocol):
      async def send_verification_email(self, *, to: str, verify_url: str) -> None: ...

  class ConsoleMailer:   # dev/default — log link qua structlog, KHÔNG gửi thật
  class CapturingMailer: # test — lưu (to, verify_url) vào list cho assert
  # SmtpMailer: TƯƠNG LAI — nối khi có hạ tầng; chưa cấu hình thì raise/khởi động fail
```

- DI: thêm `mailer` vào `app/api/deps.py` giống `auth_service`; chọn adapter theo
  `settings.environment` (dev/test → Console/Capturing; production chưa có SMTP →
  fail-fast rõ ràng để không "âm thầm không gửi" trên prod).
- Config mới trong `Settings`:
  - `frontend_base_url: str = "http://localhost:3000"` — dựng link
    `"{frontend_base_url}/verify-email?token={raw}"`.
  - `verification_token_ttl_hours: int = 24`.
  - Rate-limit resend: tái dùng bucket `rate_limit_register_*` hoặc thêm
    `rate_limit_resend_*` (mặc định 5/giờ, khớp register).

> Link verify trỏ tới **trang FE** (`/verify-email?token=...`), trang đó **POST**
> token lên `/auth/verify-email`. Token nằm trong query URL là khó tránh với link
> email; giảm thiểu bằng **single-use + TTL ngắn (24h)**. Ghi rõ ở §6 risk.

## 5. Phân tích an toàn enumeration (trọng tâm — không tái mở oracle)

| Bề mặt mới | Nguy cơ enumeration | Thiết kế chống |
|---|---|---|
| `register` | 202-vs-khác cho email trùng | **Luôn 202** + body chung; nhánh trùng vẫn burn bcrypt (`_DUMMY_HASH`) cân timing; không phiên. Giữ nguyên H-04. |
| `resend-verification` | "đã gửi" vs "email không tồn tại / đã verify" | **Luôn 202** chung chung. Nội bộ: chỉ thực sự gửi nếu user tồn tại & chưa verify; mọi nhánh khác là no-op cùng latency (burn 1 thao tác tương đương). Rate-limited để chặn quét. |
| `verify-email` | "token sai" vs "token đúng nhưng hết hạn/đã dùng" có khác nhau? | Một class lỗi **chung** (`TokenError`/`400` generic) cho mọi nhánh sai. Không tiết lộ token tồn tại hay chỉ hết hạn. |
| `login` | `403 email_not_verified` lộ email tồn tại | Chỉ phát SAU khi **pw đúng** (caller đã chứng minh sở hữu credential). Pw sai → `401` chung + dummy verify. Không phải pre-auth oracle. |

Bất biến đo được: một bộ test enumeration chạy email-mới vs email-trùng vs
email-không-tồn-tại qua `register`/`resend` và assert **status + body + (xấp xỉ)
timing** không phân biệt.

## 6. Kế hoạch kiểm thử & blast radius

### 6.1 Blast radius (đã đo)

- **~10 helper `_register` integration** (`test_guardian_api`, `test_school_api`,
  `test_wellbeing_api`, `test_competency_api`, `test_assessment_api`,
  `test_reco_g6_relational`, `test_content_editor_api`, `test_school_admin_api`,
  …) hiện `assert resp.status_code == 201` rồi login ngay. Tất cả sẽ hỏng vì
  (a) status đổi 202, (b) login bị chặn tới khi verify.
  → **Giải pháp:** một helper dùng chung trong `tests/conftest.py`:
  `register_and_verify(client, mailer, **kw)` — register (202) → lấy token từ
  `CapturingMailer` → verify (204) → trả payload. Các file đổi `_register` để gọi
  helper này (sửa cơ học, một khuôn).
- **H-04 tests** `test_register_duplicate_email_indistinguishable_pt04` &
  `test_register_duplicate_under16_indistinguishable_pt04` (`test_auth_api.py`):
  đổi assert `201`→`202`, **giữ nguyên** ý nghĩa bất khả phân biệt.
- **FE** `frontend/features/auth/RegisterForm.tsx`: bỏ auto-login; sau register
  hiện màn "kiểm tra email". Trang mới `/verify-email` gọi endpoint verify. Nút
  resend. (E2E + Storybook cập nhật theo full-stack profile.)

### 6.2 Test mới (backend, NFR-19: 100% line+branch trên auth code mới)

- Unit (`tests/unit/`): phát hành token (hash-only, TTL), single-use (dùng lại →
  từ chối), hết hạn → từ chối, resend vô hiệu token cũ.
- Integration (`tests/integration/test_auth_api.py` + mới):
  - register → 202, không cấp cookie/phiên, không trả `UserOut`.
  - login trước verify → `403 email_not_verified`; sau verify → phiên OK.
  - verify token sai/hết hạn/đã dùng → lỗi chung; verify đúng → 204 + login được.
  - resend luôn 202 (email tồn tại / không tồn tại / đã verify) — enumeration-safe.
  - **compose guardian:** under-16 verify email nhưng chưa consent → vẫn
    `PENDING_GUARDIAN_CONSENT`, không xử lý dữ liệu nhạy cảm; sau consent → ACTIVE.
  - enumeration suite (status+body+timing) cho register/resend.
- Property/edge: token urlsafe, race verify đồng thời (single-use giữ vững).

### 6.3 Sabotage (bắt buộc, /formal-verify Hard Rule 1)

- Tạm cho `login` bỏ chốt `email_verified_at` → test "login trước verify bị chặn"
  PHẢI fail. Hoàn tác.
- Tạm cho `verify-email` chấp nhận token đã `consumed_at` → test single-use PHẢI
  fail. Hoàn tác.

## 7. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|---|---|
| Migration khoá hết user cũ (email_verified_at NULL) | Backfill `= created_at` trong `upgrade()`; chỉ user MỚI đi verify (§3.2). |
| Không SMTP trên prod → "âm thầm không gửi" | Adapter prod **fail-fast** khi chưa cấu hình; dev/test dùng Console/Capturing (§4). |
| Token trong URL email (history/referrer leak) | Single-use + TTL 24h; link tới trang FE POST token, không GET tác dụng phụ (§4). |
| Tái mở enumeration trên bề mặt mới | §5 + enumeration test suite khoá status/body/timing. |
| Blast radius test lớn | Một helper `register_and_verify` dùng chung; sửa cơ học theo khuôn (§6.1). |
| H-04 squatting vẫn khoá chủ thật trong TTL | Tài khoản chưa verify hết hạn & được dọn (purge job tương lai) trả email về; tài liệu hoá là known-limitation MVP. |

## 8. Ngoài phạm vi (N-3 KHÔNG làm)

- Gửi email SMTP thật (port sẵn sàng, adapter prod nối sau).
- Job dọn tài khoản chưa verify quá hạn (đề xuất N-tiếp; MVP để token hết hạn là đủ).
- Đổi luồng guardian-consent (chỉ compose, không sửa).
