# Sơ đồ Luồng Dữ liệu — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29

> Neo vào [`docs/spec.md`](../spec.md) §8 (CP-1…CP-8) và [`docs/legal/legal-basis.md`](../legal/legal-basis.md). Các luồng nhấn mạnh **cổng đồng ý giám hộ**, **xử lý dữ liệu nhạy cảm + audit**, và **gợi ý human-in-the-loop**.

---

## Luồng dữ liệu cấp hệ thống

```mermaid
flowchart TD
    subgraph "Client"
        BROWSER["Browser\n(Student/Guardian/Counselor)"]
        LOCALMEM["Memory\n(access_token)"]
        COOKIE["httpOnly Cookie\n(refresh_token)"]
    end
    subgraph "Nginx (Edge)"
        RATELIMIT["Rate Limiter\n(limit_req)"]
        STATICFILE["Static File Server\n(Frontend Bundle)"]
        PROXY["Reverse Proxy\n/api/* → backend:8000"]
        SECHEADERS["Security Headers\nCSP, HSTS, X-Frame"]
    end
    subgraph "Backend API"
        MIDDLEWARE["Middleware\nCorrelation ID · timing · CORS"]
        AUTHDEP["Auth Dependency\nJWT validation · inject actor"]
        CONSENT["Consent Guard\n<16 ⇒ cần GuardianConsent active (CP-1)"]
        RBAC["RBAC/Scope\nguardian↔child · counselor↔student (CP-4)"]
        HANDLER["Route Handler"]
        SERVICE["Service Layer\nlogic · ownership · consent"]
        REPO["Repository Layer"]
        CRYPTO["Field Crypto\n(kết quả nhạy cảm)"]
        AUDIT["Audit Writer\n1 audit / đọc nhạy cảm (CP-3)"]
        LOGGER["Structured Logger\nNDJSON (không log PII/nhạy cảm)"]
    end
    subgraph "Persistence"
        DB[("DB (SQLite→Postgres)\nusers · guardian_consent\nassessment_result(enc)\ncompetency · careers · reco")]
        AUDITDB[("Audit Store\nappend-only")]
    end

    BROWSER -->|"HTTPS GET / (static)"| RATELIMIT --> STATICFILE -->|"bundle"| BROWSER
    BROWSER -->|"HTTPS /api/v1/*\nBearer {token}"| RATELIMIT --> SECHEADERS --> PROXY --> MIDDLEWARE --> AUTHDEP
    AUTHDEP --> CONSENT --> RBAC --> HANDLER --> SERVICE --> REPO --> DB
    SERVICE -. "đọc/ghi kết quả nhạy cảm" .-> CRYPTO
    HANDLER -. "đọc dữ liệu nhạy cảm" .-> AUDIT --> AUDITDB
    DB -->|"rows"| REPO --> SERVICE --> HANDLER -->|"JSON"| BROWSER
    MIDDLEWARE -->|"log request"| LOGGER
    BROWSER -->|"token"| LOCALMEM
    BROWSER -->|"cookie auto"| COOKIE
```

---

## Luồng xác thực (Authentication)

```mermaid
flowchart LR
    subgraph "Login"
        CREDS["email + password"]
    end
    subgraph "Backend — Auth Service"
        LOOKUP["DB lookup by email"]
        BCRYPT["bcrypt.checkpw\n(timing-safe)"]
        JWTGEN["JWT\nsub:user_id · exp:+15m\njti:uuid · iss:weup-api"]
        RTGEN["Refresh token\nrandom 32B · SHA-256\nlưu hash"]
    end
    subgraph "Response"
        BODY["JSON: access_token + profile\n(+ account_status)"]
        HCOOKIE["Set-Cookie: refresh_token=… (7d)"]
    end
    CREDS --> LOOKUP --> BCRYPT --> JWTGEN & RTGEN
    JWTGEN --> BODY
    RTGEN --> HCOOKIE
```

> Nếu `account_status = pending_guardian_consent`, đăng nhập thành công nhưng frontend **chặn route dữ liệu hướng nghiệp** và điều hướng tới luồng giám hộ.

---

## ⭐ Luồng đăng ký + Đồng ý giám hộ (<16) — CP-1/CP-2

```mermaid
flowchart TD
    REG["Đăng ký: email, password, date_of_birth"] --> AGE{"age_band?"}
    AGE -->|"≥16 (adult/16_17)"| ACTIVE["account_status = active\n→ dùng đầy đủ"]
    AGE -->|"under_16"| PENDING["account_status = pending_guardian_consent\n⛔ KHÔNG xử lý dữ liệu hướng nghiệp"]
    PENDING --> INVITE["Trẻ nhập thông tin người giám hộ\nPOST /guardians/invite"]
    INVITE --> VERIFY["Guardian xác nhận qua kênh độc lập\n(email / VNeID)"]
    VERIFY --> CONSENT["Tạo GuardianConsent status=active\nPOST /guardians/consent"]
    CONSENT --> UNLOCK["account_status = active\n→ trắc nghiệm/gợi ý mở khóa"]
    UNLOCK --> REVOKE{"Guardian thu hồi?"}
    REVOKE -->|"có"| BACK["consent=revoked\n→ về pending; dừng xử lý MỚI (CP-2)"]
    REVOKE -->|"không"| OK["tiếp tục"]
    BACK --> CONSENT
```

**Bất biến (TLA+ ConsentLifecycle):** không có `AssessmentResult`/`Recommendation` nào của user `under_16` được tạo khi không có consent `active` (CP-1); sau thu hồi, không xử lý mới đến khi active lại (CP-2).

---

## ⭐ Luồng làm trắc nghiệm (RIASEC/VIPS/MBTI) — dữ liệu nhạy cảm + audit

```mermaid
flowchart TD
    START["Học sinh mở /assessments/{type}"] --> GATE{"consent OK?\n(CP-1)"}
    GATE -->|"không (<16, chưa consent)"| BLOCK["403 GUARDIAN_CONSENT_REQUIRED"]
    GATE -->|"có"| SUBMIT["POST /assessments/{type}/submit\n(câu trả lời)"]
    SUBMIT --> SCORE["Service chấm điểm\n(RIASEC/VIPS/MBTI)"]
    SCORE --> ENC["Field Crypto: mã hóa payload\nis_sensitive=true, version++"]
    ENC --> SAVE["Lưu AssessmentResult (encrypted)"]
    SAVE --> EXPLAIN["Trả kết quả + GIẢI THÍCH\n(không kết luận cứng 1 nghề)"]
    EXPLAIN --> READ["Mỗi lần đọc kết quả về sau"]
    READ --> AUDIT["Audit Writer: 1 audit_log\nis_sensitive_access=true (CP-3)"]
    AUDIT --> SHOW["Hiển thị (student / guardian / counselor theo RBAC)"]
```

> Kết quả gắn `competency_code` (chủ yếu NL1) + `dieu5_code=b`. Item ưu tiên nguồn **ILO Việt Nam** (sources.md §2). Người dùng/guardian có thể **xuất/xóa** (quyền chủ thể dữ liệu).

---

## Luồng thư viện nghề (Career Library) — Điều 5(a)

```mermaid
flowchart TD
    FILTER["Filter: nhóm RIASEC · lĩnh vực · trình độ đào tạo"] -->|"debounced"| REQ["GET /api/v1/careers?riasec=…&field=…"]
    REQ --> PARSE["Validate query (Pydantic)"]
    PARSE --> QUERY["Query CareerProfile\nWHERE riasec_codes overlap …\nORDER BY relevance"]
    QUERY --> RESP["PaginatedResponse {items,total,page}"]
    RESP --> LINK["Liên kết: kết quả RIASEC → nghề gợi ý liên quan"]
```

> Thư viện nghề **versioned**, rà soát/cập nhật định kỳ (TT 16/2026); bao gồm nhánh GDNN & "trường trung học nghề" (Luật GDNN 124/2025).

---

## ⭐ Luồng gợi ý có giải thích (Human-in-the-loop) — CP-5/CP-6

```mermaid
flowchart TD
    TRIGGER["Yêu cầu gợi ý\n(POST /recommendations)"] --> INPUT["Thu thập: hồ sơ + kết quả test + tiến bộ năng lực"]
    INPUT --> GEN["Recommendation Engine sinh gợi ý"]
    GEN --> RAT{"có rationale?\n(CP-6)"}
    RAT -->|"không"| REJECT["Từ chối tạo (vi phạm CP-6)"]
    RAT -->|"có"| CREATE["Tạo Recommendation\nstatus=proposed\nrequires_human_confirmation=true"]
    CREATE --> DISPLAY["Hiển thị: gợi ý + LÝ DO\n+ cảnh báo 'quyết định thuộc về bạn/giám hộ/GV'"]
    DISPLAY --> HUMAN{"Người xác nhận\n(student/guardian/counselor)"}
    HUMAN -->|"accepted/rejected/deferred"| CONFIRM["POST /recommendations/{id}/confirm\nconfirmed_by = người"]
    CONFIRM --> APPLY["Chỉ khi accepted (do người) mới đưa vào lộ trình"]
    HUMAN -. "hệ thống KHÔNG tự áp dụng" .-> NOOP["(không hành động tự động)"]
```

**Bất biến (TLA+ RecommendationGovernance):** không gợi ý nào thiếu `rationale` (CP-6); không gợi ý nào có hiệu lực khi chưa có người xác nhận (CP-5). Trùng khớp nguyên tắc **không ép buộc phân luồng** (TT 16/2026) + **AI có kiểm soát** (Luật 134/2025 Đ.4).

---

## Luồng Correlation & Observability

```mermaid
flowchart LR
    subgraph "Nginx"
        GEN_ID["Generate X-Request-ID"]
    end
    subgraph "Backend Middleware"
        EXTRACT["Extract X-Request-ID"]
        BIND["Bind structlog ctx:\nrequest_id · actor_id · path · method"]
    end
    subgraph "Log Pipeline"
        STRUCTLOG["structlog JSON\n(redact PII/nhạy cảm)"]
        STDOUT["stdout (NDJSON)"]
        SHIP["Log shipper (Vector/Fluentd, sau)"]
    end
    GEN_ID --> EXTRACT --> BIND -->|"mọi log kế thừa ctx"| STRUCTLOG --> STDOUT --> SHIP
    BIND --> RESP["Response header X-Request-ID"]
```

---

## Luồng xóa mềm tài khoản & quyền chủ thể dữ liệu

```mermaid
flowchart TD
    REQ["Người dùng/guardian yêu cầu xóa\nDELETE /me hoặc /me/assessments/{id}"] --> SOFT["Soft delete\n(is_deleted=true, cửa sổ khôi phục)"]
    SOFT --> EXPORT["Hỗ trợ xuất dữ liệu cá nhân (Luật 91/2025)"]
    SOFT --> PURGE["Purge job định kỳ\nxóa cứng sau cửa sổ khôi phục"]
    SOFT --> AUDIT["Ghi audit thay đổi (NFR-16)"]
```

> Với trẻ <16, **guardian** thực hiện được quyền xóa/xuất thay trẻ. Thu hồi consent (CP-2) là một dạng dừng xử lý, khác với xóa dữ liệu.
