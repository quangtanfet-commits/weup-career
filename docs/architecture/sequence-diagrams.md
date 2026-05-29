# Sơ đồ Tuần tự (Sequence Diagrams) — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29

> Neo vào [`docs/spec.md`](../spec.md) (FR + CP). Nhấn mạnh cổng giám hộ <16, xử lý dữ liệu nhạy cảm + audit, và gợi ý human-in-the-loop.

---

## Auth — Đăng ký (có cổng tuổi)

```mermaid
sequenceDiagram
    autonumber
    actor U as Người dùng (Browser)
    participant FE as Frontend SPA
    participant N as Nginx
    participant API as Backend API
    participant DB as Database

    U->>FE: Điền form đăng ký (email, password, date_of_birth)
    FE->>FE: Validate Zod (client)
    FE->>N: POST /api/v1/auth/register
    N->>API: Proxy (X-Request-ID)
    API->>API: Validate (Pydantic); suy ra age_band
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: NULL (email khả dụng)
    API->>API: bcrypt hash (cost=12)
    alt age_band = under_16
        API->>DB: INSERT user (account_status=pending_guardian_consent)
        API-->>FE: 201 {id, account_status:"pending_guardian_consent"}
        FE-->>U: Điều hướng → luồng mời giám hộ
    else age_band ≥ 16
        API->>DB: INSERT user (account_status=active)
        API-->>FE: 201 {id, account_status:"active"}
        FE-->>U: Điều hướng → dashboard
    end
```

---

## ⭐ Đồng ý giám hộ (<16) — CP-1/CP-2

```mermaid
sequenceDiagram
    autonumber
    actor C as Học sinh <16
    actor G as Người giám hộ
    participant FE as Frontend
    participant API as Backend API
    participant DB as Database

    C->>FE: Nhập thông tin giám hộ (email/SĐT)
    FE->>API: POST /api/v1/guardians/invite
    API->>DB: Tạo GuardianLink (chưa verified)
    API-->>G: Gửi lời mời qua kênh độc lập (email / VNeID)
    G->>FE: Mở liên kết xác nhận
    G->>API: POST /api/v1/guardians/consent
    API->>API: Xác thực danh tính giám hộ (email/VNeID)
    API->>DB: GuardianLink.verified_at = NOW(); tạo GuardianConsent(status=active)
    API->>DB: UPDATE user SET account_status=active
    API-->>FE: 200 {consent: active}
    FE-->>C: Mở khóa trắc nghiệm & gợi ý

    Note over G,API: Bất cứ lúc nào — thu hồi:
    G->>API: POST /api/v1/guardians/consent/revoke
    API->>DB: GuardianConsent.status=revoked; user→pending
    API-->>FE: 200 — dừng xử lý dữ liệu MỚI (CP-2)
```

---

## Auth — Đăng nhập & phát hành token

```mermaid
sequenceDiagram
    autonumber
    actor U as Người dùng
    participant FE as Frontend SPA
    participant API as Backend API
    participant DB as Database

    U->>FE: Submit (email, password)
    FE->>API: POST /api/v1/auth/login
    API->>DB: SELECT user WHERE email = ?
    DB-->>API: User row (hoặc null)
    alt Không tồn tại / inactive
        API-->>FE: 401 {INVALID_CREDENTIALS} (generic — chống enumeration)
    else Hợp lệ
        API->>API: bcrypt.checkpw
        API->>API: JWT access (exp 15m) + refresh token (random, lưu SHA-256)
        API->>DB: INSERT refresh_token
        API-->>FE: 200 {access_token, user, account_status}\nSet-Cookie: refresh_token (httpOnly,Secure,SameSite=Strict)
        FE->>FE: Lưu access_token in-memory (Zustand)
        alt account_status = pending_guardian_consent
            FE-->>U: → luồng giám hộ
        else active
            FE-->>U: → dashboard
        end
    end
```

---

## Auth — Refresh token im lặng (CP-7)

```mermaid
sequenceDiagram
    autonumber
    participant FE as Frontend (Axios interceptor)
    participant API as Backend API
    participant DB as Database

    Note over FE: Timer 60s trước khi access_token hết hạn
    FE->>API: POST /api/v1/auth/refresh (Cookie: refresh_token)
    API->>API: SHA-256 hash token
    API->>DB: SELECT refresh_token WHERE hash=? AND revoked_at IS NULL AND expires_at>NOW()
    alt Hợp lệ
        DB-->>API: Token record
        API->>DB: UPDATE old SET revoked_at=NOW() + INSERT new (cùng transaction — nguyên tử)
        API->>API: JWT access mới
        API-->>FE: 200 {access_token} + Set-Cookie refresh mới
    else Hết hạn/thu hồi
        API-->>FE: 401 {TOKEN_EXPIRED}
        FE->>FE: Clear auth → /login
    end
```

---

## ⭐ Làm trắc nghiệm RIASEC/VIPS/MBTI — dữ liệu nhạy cảm + audit (CP-1, CP-3)

```mermaid
sequenceDiagram
    autonumber
    actor U as Học sinh
    participant FE as Frontend
    participant API as Backend API
    participant CG as Consent Guard
    participant CR as Field Crypto
    participant AU as Audit Writer
    participant DB as Database

    U->>FE: Mở /assessments/riasec, làm bài
    FE->>API: POST /api/v1/assessments/riasec/submit
    API->>CG: Kiểm tra consent (CP-1)
    alt <16 && consent != active
        CG-->>FE: 403 GUARDIAN_CONSENT_REQUIRED
    else OK
        API->>API: Chấm điểm RIASEC
        API->>CR: Mã hóa result_payload
        CR-->>API: ciphertext
        API->>DB: INSERT AssessmentResult (encrypted, is_sensitive=true, version++)
        API-->>FE: 201 {result + giải thích} (không kết luận cứng 1 nghề)
    end

    Note over U,DB: Mỗi lần đọc kết quả về sau
    U->>FE: Xem lại kết quả
    FE->>API: GET /api/v1/me/assessments/{id}
    API->>AU: Ghi audit_log (is_sensitive_access=true) — CP-3
    API->>CR: Giải mã payload
    API-->>FE: 200 {result}
```

---

## ⭐ Gợi ý có giải thích — Human-in-the-loop (CP-5, CP-6)

```mermaid
sequenceDiagram
    autonumber
    actor U as Học sinh
    actor H as Người xác nhận\n(student/guardian/counselor)
    participant FE as Frontend
    participant API as Backend API
    participant RE as Recommendation Engine
    participant DB as Database

    U->>FE: Yêu cầu gợi ý lộ trình
    FE->>API: POST /api/v1/recommendations
    API->>RE: Hồ sơ + kết quả test + tiến bộ năng lực
    RE-->>API: Gợi ý + rationale (giải thích)
    alt rationale rỗng
        API-->>FE: 422 (vi phạm CP-6 — từ chối)
    else có rationale
        API->>DB: INSERT Recommendation (status=proposed, requires_human_confirmation=true)
        API-->>FE: 201 {payload, rationale, "quyết định thuộc về bạn/giám hộ/GV"}
    end
    H->>FE: Xem gợi ý + lý do, chọn accepted/rejected/deferred
    FE->>API: POST /api/v1/recommendations/{id}/confirm
    API->>DB: UPDATE status, confirmed_by=H (CP-5)
    API-->>FE: 200
    Note over API,DB: Hệ thống KHÔNG tự áp dụng — chỉ khi accepted (do người)
```

---

## Counselor — Tư vấn 3 tầng (CP-4 RBAC)

```mermaid
sequenceDiagram
    autonumber
    actor CO as Counselor
    participant API as Backend API
    participant AZ as RBAC/Scope
    participant DB as Database

    CO->>API: GET /api/v1/school/{id}/students
    API->>AZ: Kiểm tra counselor↔student trong school_id (CP-4)
    alt Ngoài phạm vi trường
        AZ-->>CO: 403 Forbidden
    else Trong phạm vi
        API->>DB: SELECT students WHERE school_id=? (dữ liệu đã gỡ nhạy cảm theo quyền)
        API-->>CO: 200 {students, tiến bộ}
        CO->>API: POST /api/v1/counseling/sessions {student_id, tier, notes}
        API->>DB: INSERT CounselingSession
        API-->>CO: 201
    end
```

---

## Health & Readiness

```mermaid
sequenceDiagram
    participant Orchestrator as Container Orchestrator
    participant API as Backend API
    participant DB as Database

    loop Mỗi 10s (liveness)
        Orchestrator->>API: GET /api/v1/health
        API-->>Orchestrator: 200 {status:"ok", uptime_s}
    end
    loop Mỗi 5s (readiness)
        Orchestrator->>API: GET /api/v1/ready
        API->>DB: SELECT 1
        alt DB ok
            API-->>Orchestrator: 200 {status:"ready", db:"ok"}
        else DB lỗi
            API-->>Orchestrator: 503 {status:"not_ready"}
            Note over Orchestrator: Không gửi traffic; restart nếu kéo dài
        end
    end
```
