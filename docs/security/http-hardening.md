# HTTP Hardening — Security Headers & Rate Limiting

**Status:** Design (pre-implementation)
**Date:** 2026-06-01
**Owner:** Backend
**Closes:** PT-03 (no rate limiting), PT-05 (missing security headers), PT-07 (Server header disclosure)
**Related:** [ADR-008 Security Controls](../adr/ADR-008-security-controls.md), [threat-model.md](./threat-model.md)

---

## 1. Mục tiêu & phạm vi

Slice này bổ sung hai lớp phòng thủ HTTP ở tầng ứng dụng (application-layer), **không phụ thuộc** vào nginx/reverse-proxy, để khắc phục drift giữa ADR-008 và hiện trạng code:

1. **Security headers** — gắn nhóm header bảo mật lên *mọi* response (kể cả lỗi).
2. **Rate limiting** — giới hạn tần suất theo bucket cho nhóm endpoint nhạy cảm.

ADR-008 hiện ghi "security headers in Nginx" và mô tả bảng rate-limit, nhưng **code chưa hề có** (main.py chỉ có `correlation_id` + CORS; không có dependency `slowapi`/`limits`). Đặt hai lớp này trong app đảm bảo phòng thủ vẫn còn hiệu lực khi chạy native (devcontainer aarch64/linuxkit không chạy được docker compose qua nginx) và khi triển khai sau proxy.

**Ngoài phạm vi:** PT-04 (email enumeration), sửa `.env`. Theo dõi riêng.

---

## 2. Security headers

### 2.1 Bộ header áp dụng

| Header | Giá trị | Áp dụng cho | Lý do |
|--------|---------|-------------|-------|
| `X-Content-Type-Options` | `nosniff` | Mọi response | Chặn MIME-sniffing → giảm XSS qua content-type nhầm lẫn |
| `X-Frame-Options` | `DENY` | Mọi response | Chặn clickjacking (đóng khung trang trong iframe) |
| `Referrer-Policy` | `no-referrer` | Mọi response | Không rò rỉ URL nội bộ/token query sang origin khác |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'; base-uri 'none'` | Mọi response **trừ** doc paths | API trả JSON, không cần tải tài nguyên nào → CSP nghiêm ngặt nhất |
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains` | Mọi response, **chỉ khi production** | Ép HTTPS 2 năm; bỏ ở dev để không phá localhost HTTP |
| `Server` | `WeUp` | Mọi response | Ghi đè `uvicorn` → chống lộ phiên bản (PT-07) |

### 2.2 Vì sao CSP miễn trừ doc paths

CSP `default-src 'none'` sẽ chặn Swagger UI và ReDoc (chúng nạp JS/CSS/font từ CDN và dùng inline script). Ba đường dẫn sau được **miễn CSP** (các header khác vẫn áp dụng):

- `/api/v1/docs` (Swagger UI)
- `/api/v1/redoc` (ReDoc)
- `/api/v1/openapi.json` (schema, do hai trang trên nạp)

Đây là tài liệu nội bộ, rủi ro thấp; việc nới CSP chỉ cho 3 path tĩnh này không mở rộng bề mặt tấn công của API JSON.

### 2.3 Vì sao HSTS chỉ bật ở production

`environment == "production"` (qua `Settings.is_production`). Ở dev/test chạy HTTP localhost; gửi HSTS sẽ khiến trình duyệt ép HTTPS và phá vỡ luồng phát triển. Quyết định theo môi trường, không hard-code.

### 2.4 Ghi đè Server header

Starlette/uvicorn mặc định trả `Server: uvicorn`. Middleware ghi đè thành `WeUp` (không kèm version). Đáp ứng PT-07 mà không cần đụng cấu hình uvicorn.

---

## 3. Rate limiting

### 3.1 Bảng bucket (khớp ADR-008)

| Nhóm endpoint | Giới hạn | Cửa sổ | Khóa (key) |
|---------------|----------|--------|------------|
| `POST /api/v1/auth/register` | 5 | 60 phút | IP |
| `POST /api/v1/auth/login` | 20 | 1 phút | IP |
| `POST /api/v1/auth/refresh` | 60 | 1 phút | IP |
| Mọi `/api/v1/*` còn lại | 200 | 1 phút | JWT `sub` nếu có, ngược lại IP |

Endpoint không thuộc `/api/v1/*` (ví dụ `/health`, doc paths) **không** bị rate-limit.

### 3.2 Thuật toán — fixed-window in-memory

Chọn **fixed-window counter** (đơn giản, không cần dependency ngoài):

- Khóa bucket = `(scope, identity)` trong đó `scope` ∈ {`register`,`login`,`refresh`,`api`} và `identity` = IP hoặc `sub`.
- Mỗi khóa giữ `(count, window_start)`. Khi request đến tại thời điểm `now`:
  - Nếu `now - window_start >= window` → reset `count=0`, `window_start=now`.
  - `count += 1`; nếu `count > limit` → từ chối 429.
- Lưu trên `app.state.rate_limiter` → mỗi `create_app()` (mỗi test) có state cô lập.

**Hạn chế đã biết (ghi rõ):** in-memory ⇒ đếm theo *từng process*. Khi chạy nhiều worker/replica, giới hạn thực tế = `limit × số worker`. Chấp nhận được cho v1 (chống brute-force/abuse thô); khi scale ngang cần chuyển sang store dùng chung (Redis) — ghi nhận là việc tương lai, không thuộc slice này. Fixed-window cũng có "burst biên cửa sổ" (tối đa 2× limit quanh ranh giới window) — chấp nhận với mục tiêu chống lạm dụng, không phải điều tiết chính xác.

### 3.3 Định danh (identity)

- **IP:** lấy từ `request.client.host`. (Sau proxy tin cậy có thể đọc `X-Forwarded-For` — chưa làm trong v1 vì chưa có proxy tin cậy; ghi nhận để tránh IP-spoofing nếu thêm sau.)
- **`sub`:** với nhóm "api", thử `decode_access_token` trên bearer; thành công thì khóa theo `sub` (công bằng giữa user sau NAT chung). Lỗi/thiếu token → fallback IP. Việc decode bọc trong try/except, không bao giờ làm request đổ vỡ.

### 3.4 Response khi vượt giới hạn

- Status `429 Too Many Requests`.
- Header `Retry-After: <giây còn lại tới hết window>`.
- Body theo đúng error envelope:
  ```json
  {"error": {"code": "RATE_LIMITED", "message": "Quá nhiều yêu cầu, thử lại sau.",
             "details": {"retry_after": 42}, "request_id": "<id>"}}
  ```
- Trả `JSONResponse` trực tiếp trong middleware (không thêm exception class) — đơn giản, và vì rate-limit chạy *trước* router nên không qua exception handler của AppError.

### 3.5 Cờ bật/tắt

- Setting `rate_limit_enabled: bool = True` (mặc định bật ở prod/dev).
- `conftest.make_settings()` đặt `rate_limit_enabled=False` để 394 test hiện có không bị nhiễu.
- Test chuyên biệt bật cờ + đặt limit thấp (vd 2) để có 429 tất định.
- Các giới hạn & cửa sổ cũng là setting (giá trị mặc định = bảng 3.1) để test ép số nhỏ.
- **Stack E2E (`docker-compose.test.yml`) cũng tắt cờ** (`RATE_LIMIT_ENABLED=false`). Sau nginx, mọi request tới backend đến từ **một** source IP, nên các bucket theo-IP (register 5/h, login 20/min) cạn trong một lần chạy suite và trả 429 — làm hỏng các luồng auth-lifecycle. Hành vi rate-limit đã được phủ tất định bởi `tests/integration/test_http_hardening.py`, nên E2E không cần kiểm thử lại.

---

## 4. Thứ tự middleware

Starlette áp middleware theo **thứ tự ngược** với `add_middleware` (cái thêm sau cùng = ngoài cùng). Mục tiêu:

```
request  ─►  [security_headers]  ─►  [CORS]  ─►  [correlation_id]  ─►  [rate_limit]  ─►  router
response ◄─  [security_headers]  ◄─  [CORS]  ◄─  [correlation_id]  ◄─  [rate_limit]  ◄─
```

Thứ tự gọi `add_middleware` (trong `create_app`), từ **trong ra ngoài**:

1. `rate_limit` — **trong cùng**: chặn sớm, nhưng *sau* khi correlation_id đã chạy ở hành trình request? Không — xem chú thích dưới.
2. `correlation_id` — đặt `request.state.request_id` để envelope 429 có id.
3. `CORS` (nếu có origin).
4. `security_headers` — **ngoài cùng**: header bám lên *mọi* response, kể cả 429 và lỗi.

> **Chú thích thứ tự rate_limit ↔ correlation_id:** ta cần `request_id` đã được gán trước khi rate_limit dựng envelope 429. Vì "thêm sau = ngoài hơn", để correlation_id bao ngoài rate_limit thì phải `add_middleware(rate_limit)` **trước** rồi `add_middleware(correlation_id)`. Như vậy ở chiều request, correlation_id chạy trước rate_limit (gán id xong mới tới giới hạn) — đúng nhu cầu. security_headers thêm sau cùng để ngoài cùng.

Thứ tự code thực tế:
```python
app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)      # innermost
app.add_middleware(BaseHTTPMiddleware, dispatch=correlation_id_middleware)
if settings.cors_origin_list:
    app.add_middleware(CORSMiddleware, ...)
app.add_middleware(BaseHTTPMiddleware, dispatch=security_headers_middleware)  # outermost
```

---

## 5. Threat mapping

| Finding | Mô tả | Khắc phục trong slice |
|---------|-------|------------------------|
| **PT-03** | Không có rate limiting → brute-force login/register, lạm dụng API | §3 — bucket login/register/refresh + global api |
| **PT-05** | Thiếu security headers (nosniff, X-Frame-Options, CSP, HSTS, Referrer-Policy) | §2 — bộ header đầy đủ trên mọi response |
| **PT-07** | `Server: uvicorn` lộ stack/phiên bản | §2.4 — ghi đè `Server: WeUp` |

PT-04 (email enumeration) **không** thuộc slice này.

---

## 6. Tác động & hệ quả

- Thêm 2 middleware BaseHTTP → mỗi request qua 4 lớp (chi phí O(1), không I/O).
- Rate limiter thêm 1 dict lookup + cập nhật counter per request; bộ nhớ bị chặn bởi số `(scope, identity)` đang hoạt động trong 1 cửa sổ — prune cơ hội khi truy cập.
- Không thay đổi `trace_emit` → **trung lập với formal verification** (CP-7 refresh lifecycle không đổi).
- Không phụ thuộc package mới — limiter tự viết, dependency-free.
- Không đổi hợp đồng API hiện có; chỉ thêm header + khả năng 429 cho client vượt ngưỡng.
