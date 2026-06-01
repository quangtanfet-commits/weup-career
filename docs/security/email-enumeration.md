# Email Enumeration — Register Response Oracle (H-04)

**Status:** Design (pre-implementation)
**Date:** 2026-06-01
**Owner:** Backend
**Hardening ID:** H-04
**Closes:** PT-04 (email enumeration via `/auth/register` conflict response)
**Related:** [auth-design.md](./auth-design.md), [http-hardening.md](./http-hardening.md), [threat-model.md](./threat-model.md)

---

## 1. Bối cảnh & finding

Pentest `weup-saas-20260531` ghi nhận **PT-04 (medium): email enumeration via `/auth/register`**. Hiện trạng `AuthService.register` (service.py:74):

```python
existing = await self._users.get_by_email(payload.email)
if existing is not None:
    raise ConflictError("Email đã được đăng ký")   # → HTTP 409
...
return user                                          # → HTTP 201 + UserOut
```

Kẻ tấn công gửi `POST /api/v1/auth/register` với một email bất kỳ và đọc status code:

- **409 Conflict** + message "Email đã được đăng ký" ⇒ email **đã tồn tại**.
- **201 Created** + `UserOut` ⇒ email **chưa tồn tại** (và vừa tạo tài khoản).

Đây là một **oracle liệt kê người dùng**: xác nhận một email có phải là khách hàng của hệ thống hay không. Với nền tảng hướng nghiệp cho học sinh (dữ liệu nhạy cảm, đối tượng <16t), việc xác nhận "email X có học sinh đăng ký" đã là rò rỉ quyền riêng tư đáng kể, độc lập với việc chiếm tài khoản.

Login đã được trung hòa chống enumeration (service.py:117-121 chạy `verify_password` trên `_DUMMY_HASH` cho email lạ để cào bằng thời gian, và luôn trả 401 `InvalidCredentialsError`). Register thì **chưa** — nó vẫn là điểm rò rỉ còn lại.

---

## 2. Ràng buộc thiết kế

Bốn ràng buộc định hình lựa chọn (đã khảo sát code trước khi thiết kế):

1. **Không có hạ tầng email.** Toàn repo không có SMTP/mailer/verify-token. Khuyến nghị nguyên văn của pentest ("luôn trả 202 + gửi email xác minh") **không khả thi trực tiếp** — nó là một tính năng lớn (email verification) chứ không phải một bản vá. Xây dựng nó nằm ngoài phạm vi slice này.

2. **Frontend bỏ qua body của register.** `RegisterForm.tsx` (onSubmit, dòng 75-93) gọi `await registerAccount(...)` **không đọc body trả về**, rồi gọi `login()` riêng và định tuyến `/consent` vs `/dashboard` dựa trên `res.user.account_status` của **login response**. ⇒ Đổi shape/nội dung response của register **không phá frontend**.

3. **Hợp đồng thành công (201 + `UserOut` có `id`) bị phụ thuộc rộng.** 32 chỗ đọc `["id"]` qua 27 lần gọi helper `_register` trong test suite assert `status_code == 201` rồi đọc `id`. ⇒ Đổi success path sang "202 + body rỗng" có blast radius lớn (sửa 27+ helper). Tránh.

4. **`/auth/register` đã bị rate-limit** 5 request / 60 phút / IP (H-03, http-hardening §3.1). ⇒ Liệt kê quy mô lớn đã bị bóp; phần còn lại là oracle mỗi-request.

---

## 3. Các phương án đã cân nhắc

| Phương án | Vì sao loại / chọn |
|-----------|--------------------|
| **A. Trả 202 + body trung lập cho mọi email** | Loại: phá hợp đồng 201+`UserOut` ở 27+ điểm test, blast radius cao; cũng cần FE/E2E rà lại dù FE bỏ qua body. |
| **B. Trả lại dữ liệu user đang tồn tại cho email trùng** | Loại: rò rỉ trực tiếp dữ liệu tài khoản người khác — tệ hơn finding gốc. |
| **C. (CHỌN) Trả `201 + UserOut` *tổng hợp, không phân biệt được* cho email trùng — no-op thuần** | Chọn: giữ success path **nguyên byte**; nhánh trùng trả về một `UserOut` dựng từ chính payload gửi lên, **không ghi DB**; blast radius tối thiểu (chỉ 1 test đổi assert). |

---

## 4. Thiết kế (Phương án C)

### 4.1 Hành vi

`register()` luôn trả `201 + UserOut`. Hai nhánh, **không phân biệt được từ phía client**:

- **Email mới (nhánh thật):** giữ **nguyên hiện tại** — tạo `User`, hash password, `self._users.add(user)`, audit `auth.register.succeeded`, trả `UserOut(user)`.
- **Email trùng (nhánh tổng hợp):** **no-op thuần** — dựng một `User` tạm trong bộ nhớ chỉ để serialize, **KHÔNG** gọi `self._users.add()`, **KHÔNG** sửa tài khoản đang tồn tại. Trả `UserOut` của user tạm đó.

### 4.2 Vì sao hai response không phân biệt được

`UserOut` gồm: `id, email, age_band, user_type, school_level, account_status, created_at`. Với nhánh tổng hợp, từng trường được dựng để **trông hệt như một đăng ký mới thành công của chính payload đó**:

| Trường | Nhánh thật | Nhánh tổng hợp (trùng) |
|--------|------------|------------------------|
| `id` | `new_uuid()` | `new_uuid()` — UUID ngẫu nhiên mới, **không** phải id của user đang tồn tại |
| `email` | `payload.email` (đã chuẩn hóa) | `payload.email` (đã chuẩn hóa) — giống nhau |
| `age_band` | `derive_age_band(payload.dob)` | `derive_age_band(payload.dob)` — cùng công thức, cùng input |
| `account_status` | derived từ age_band (FR-02) | derived từ age_band — **cùng logic** |
| `user_type` / `school_level` | từ payload | từ payload — giống nhau |
| `created_at` | `utcnow()` (model default) | `utcnow()` |

Vì mọi trường đều **suy ra từ payload do attacker gửi** (không phải từ bản ghi DB), response cho email-trùng giống hệt response cho cùng-payload-email-mới. Attacker không thể dùng id, account_status hay bất kỳ trường nào để phân biệt. **Quan trọng:** `id` PHẢI là `new_uuid()` ngẫu nhiên — không bao giờ là id thật của user đang tồn tại (nếu không lại thành oracle/rò rỉ).

### 4.3 Cào bằng thời gian (timing equalisation)

Nhánh thật tốn một lần `hash_password` (bcrypt, ~tốn CPU theo `bcrypt_rounds`). Nhánh tổng hợp nếu bỏ qua bước này sẽ **nhanh hơn rõ rệt** → tạo lại oracle qua thời gian phản hồi. Khắc phục: nhánh tổng hợp chạy một bcrypt "giả" trên `_DUMMY_HASH` (mượn đúng pattern của login, service.py:120) để tiêu cùng lượng CPU. Dùng lại hằng số `_DUMMY_HASH` sẵn có.

### 4.4 Audit (chỉ phía phòng thủ)

Nhánh tổng hợp ghi `auth.register.duplicate_suppressed` (actor_id = id của user đang tồn tại, target = user đó). Log này:

- **Người phòng thủ thấy** — phát hiện ai đang dò email, phục vụ điều tra/giám sát.
- **Attacker KHÔNG thấy** — không lộ qua response.

Nhánh thật giữ `auth.register.succeeded` như cũ.

### 4.5 Trung lập với formal verification

`register()` không phát `trace_emit` (chỉ login/refresh/logout liên quan CP-7 mới emit). Nhánh tổng hợp cũng không emit, không đụng token lifecycle ⇒ **trung lập** với 6 module TLA+ / Gate B. Không cần re-verify.

---

## 5. Rủi ro tồn dư (accepted residual)

Phương án C đóng **oracle register-response** (201-vs-409) — đúng phần mô tả trong PT-04. Còn lại hai dư lượng **vốn có với mọi hệ thống không xác minh email**:

1. **Account-squatting oracle gián tiếp:** attacker có thể đăng ký email rồi thử login bằng mật khẩu vừa đặt; nếu login *của chính họ* không cho session như mong đợi, có thể suy luận. Nhưng điều này đòi hỏi attacker đã *thử chiếm* email và chỉ phân biệt được sau một chuỗi nhiều bước — đắt hơn nhiều, và bị bóp bởi rate-limit register (5/h) + login (20/min).

2. **Login-chain:** bản thân login đã trung hòa enumeration (§1), nên không thêm oracle mới.

**Kết luận tồn dư:** Khắc phục triệt để 100% = **email verification** (đăng ký luôn 202, tài khoản chỉ kích hoạt sau khi bấm link email) — một tính năng tương lai, cần hạ tầng mailer. Ghi nhận là việc tương lai. Với rate-limit hiện có + oracle chính đã đóng, rủi ro tồn dư ở mức **chấp nhận được** cho v1, hạ PT-04 từ medium xuống residual-low.

---

## 6. Kiểm thử

Cập nhật + bổ sung trong `tests/integration/test_auth_api.py`:

1. **Sửa** `test_register_duplicate_email_409` → `test_register_duplicate_email_indistinguishable`: đăng ký email X, đăng ký lại X ⇒ **lần hai cũng 201**, body cùng shape `UserOut` (cùng `email`, có `id` hợp lệ, `account_status` đúng theo tuổi), và `id` lần hai **khác** id lần đầu (UUID mới, không lộ id thật).
2. **No-op DB:** sau hai lần đăng ký cùng email, chỉ có **một** user trong DB (login bằng mật khẩu lần đầu vẫn hoạt động; mật khẩu lần hai KHÔNG ghi đè) ⇒ chứng minh nhánh trùng không persist/không sửa tài khoản.
3. **Audit:** lần đăng ký trùng ghi `auth.register.duplicate_suppressed` (qua audit repo/log), không ghi `auth.register.succeeded`.
4. **Indistinguishability shape:** so sánh tập khóa JSON của response mới-vs-trùng cho cùng payload ⇒ giống hệt (cùng keys, cùng kiểu giá trị).

Timing equalisation không assert bằng wall-clock (flaky); thay vào đó test xác minh **đường dẫn code** chạy bcrypt giả (vd: nhánh trùng vẫn gọi verify trên dummy hash — kiểm qua việc cả hai nhánh đều tốn một thao tác hash, hoặc đơn giản assert hành vi no-op + indistinguishable shape, coi timing là thuộc tính thiết kế đã lập luận ở §4.3).

---

## 7. Tác động & hệ quả

- **API contract:** `/auth/register` không còn trả 409 cho email trùng — luôn 201. Client hiện có (FE bỏ qua body) không bị ảnh hưởng. Tài liệu OpenAPI cập nhật (bỏ 409 khỏi register responses).
- **Blast radius test:** chỉ `test_register_duplicate_email_409` đổi; 27 helper `_register` khác vẫn thấy 201 như cũ.
- **Bảo mật:** đóng oracle enumeration chính của register; audit mới giúp phát hiện dò email.
- **Không package mới**, không đụng formal verification, không đụng token lifecycle.
