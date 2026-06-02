# Tổng quan Kiến trúc Hệ thống — WeUp Career

**Phiên bản:** 2.0.0 | **Trạng thái:** APPROVED FOR REVIEW | **Ngày:** 2026-05-29
**Thay thế:** v1.0.0 (kiến trúc Todo app — placeholder)

> Neo vào [`docs/spec.md`](../spec.md) (data model §5, CP §8), [`docs/research/career-frameworks-synthesis.md`](../research/career-frameworks-synthesis.md) (mô hình 2 trục), [`docs/legal/legal-basis.md`](../legal/legal-basis.md) (consent <16, dữ liệu nhạy cảm, AI governance). Quy ước: văn xuôi tiếng Việt, định danh kỹ thuật tiếng Anh.

---

## Mô hình C4

### Level 1 — System Context

```mermaid
C4Context
    title System Context — WeUp Career (Nền tảng Hướng nghiệp Quốc gia)

    Person(student, "Học sinh", "THCS/THPT; làm trắc nghiệm, khám phá nghề, xem gợi ý lộ trình")
    Person(guardian, "Người giám hộ", "Cha/mẹ/giám hộ; đồng ý & đồng xem hồ sơ trẻ <16")
    Person(counselor, "Tư vấn học đường", "Tư vấn 3 tầng, theo dõi tiến bộ học sinh trong trường")
    Person(schoolAdmin, "Quản trị trường", "Quản lý lớp/học sinh/counselor")
    Person(operator, "Operator", "DevOps/SRE vận hành, xử lý quyền chủ thể dữ liệu")

    System(weup, "WeUp Career", "Hướng nghiệp số: trắc nghiệm (RIASEC/VIPS/MBTI), thư viện nghề, đo năng lực K-A-R, gợi ý ngành/nghề có giải thích (human-in-the-loop)")

    System_Ext(csdlGD, "CSDL Quốc gia về GD&ĐT", "NĐ 88/2026 — hồ sơ học tập, mã định danh (adapter, giai đoạn sau)")
    System_Ext(laborMarket, "HTTT Thị trường lao động", "Xu hướng việc làm, nhu cầu ngành (adapter)")
    System_Ext(vneid, "VNeID", "Xác thực tuổi & quan hệ giám hộ (NĐ 69/2024)")
    System_Ext(ci, "GitHub Actions", "Quality gate: test, security, bias test, TLC")
    System_Ext(registry, "Container Registry", "GHCR — lưu Docker images")

    Rel(student, weup, "Sử dụng", "HTTPS / Browser")
    Rel(guardian, weup, "Đồng ý/đồng xem", "HTTPS")
    Rel(counselor, weup, "Tư vấn/theo dõi", "HTTPS")
    Rel(schoolAdmin, weup, "Quản trị trường", "HTTPS")
    Rel(operator, weup, "Vận hành, giám sát", "SSH / docker compose")
    Rel(weup, vneid, "Xác thực tuổi/giám hộ (tùy chọn)", "OIDC")
    Rel(weup, csdlGD, "Liên thông hồ sơ (sau)", "API có kiểm soát")
    Rel(weup, laborMarket, "Lấy xu hướng nghề (sau)", "API")
    Rel(ci, registry, "Push images")
```

> **Ràng buộc context:** một tỷ lệ đáng kể người dùng là **học sinh <16 tuổi** → mọi luồng dữ liệu phải đi qua **cổng đồng ý giám hộ** (CP-1). Gợi ý nghề là **hệ thống AI có kiểm soát** → bắt buộc giải thích được + human-in-the-loop (CP-5/CP-6).

---

### Level 2 — Container Diagram

```mermaid
C4Container
    title Container Diagram — WeUp Career

    Person(student, "Học sinh / Giám hộ / Counselor", "Web browser")

    Container(nginx, "Nginx Reverse Proxy", "nginx:alpine", "TLS termination, static serving, /api routing, rate limiting L7")
    Container(frontend, "Frontend", "Next.js 16 App Router / React 19 / TS", "RSC public Điều 5a (SEO) + client app; REST + JSON; phân tầng UI theo school_level")
    Container(backend, "Backend API", "Python 3.12 / FastAPI / Uvicorn", "REST API; JWT; consent gate; xử lý dữ liệu nhạy cảm; audit")
    Container(recsvc, "Recommendation Engine", "Python module / service", "Gợi ý ngành/nghề/lộ trình CÓ GIẢI THÍCH; bias-tested; không tự quyết")
    ContainerDb(database, "Database", "SQLite 3.45 (MVP) → PostgreSQL", "Lưu trữ; trường nhạy cảm mã hóa; abstract qua SQLAlchemy")
    ContainerDb(audit, "Audit Store", "append-only (bảng/log)", "Audit truy cập dữ liệu nhạy cảm, consent, gợi ý (NFR-16)")

    Rel(student, nginx, "HTTPS", "TLS 1.3")
    Rel(nginx, frontend, "Proxies tới Next.js runtime (RSC/SSR + static assets)", "HTTP nội bộ")
    Rel(nginx, backend, "Proxies /api/*", "HTTP nội bộ")
    Rel(backend, database, "Read/write", "SQLAlchemy async")
    Rel(backend, recsvc, "Yêu cầu gợi ý (+rationale)", "nội bộ")
    Rel(backend, audit, "Ghi mọi truy cập nhạy cảm", "append-only")
```

> **Quyết định stack** giữ theo ADR-001/002/003: FastAPI + React/TS + SQLAlchemy, SQLite (MVP) → PostgreSQL khi scale (xem [`docs/scalability/strategy.md`](../scalability/strategy.md)). `Recommendation Engine` tách module để cô lập ranh giới AI governance (giải thích/bias/human-in-the-loop).

---

### Level 3 — Component Diagram — Backend API

```mermaid
C4Component
    title Component Diagram — Backend API (FastAPI)

    Container_Boundary(api, "Backend API") {
        Component(router, "API Router", "FastAPI Routers", "Định tuyến; prefix /api/v1")
        Component(authMw, "Auth Middleware", "DI dependency", "Validate Bearer JWT; inject current_user")
        Component(consentGuard, "Consent Guard", "core/consent.py", "Chặn xử lý dữ liệu hướng nghiệp của <16 khi chưa có GuardianConsent active (CP-1)")
        Component(rbac, "RBAC / Scope", "core/authz.py", "Phân quyền guardian↔child, counselor↔student theo school_id (CP-4)")
        Component(audit, "Audit Writer", "core/audit.py", "Ghi 1 audit/lần đọc dữ liệu nhạy cảm (CP-3)")
        Component(authH, "Auth Handler", "auth/router.py", "register/login/logout/refresh/me")
        Component(guardianH, "Guardian Handler", "guardians/router.py", "invite/consent/revoke")
        Component(assessH, "Assessment Handler", "assessments/router.py", "RIASEC/VIPS/MBTI submit + đọc kết quả (nhạy cảm)")
        Component(compH, "Competency Handler", "competency/router.py", "Cây 12 năng lực; tiến bộ K-A-R")
        Component(careerH, "Career Info Handler", "careers/router.py", "Thư viện ngành/nghề (Điều 5a)")
        Component(recH, "Recommendation Handler", "reco/router.py", "Sinh & xác nhận gợi ý (CP-5/CP-6)")
        Component(counselH, "Counseling Handler", "counseling/router.py", "Phiên tư vấn 3 tầng")
        Component(svc, "Service Layer", "*/service.py", "Logic nghiệp vụ thuần Python; kiểm tra quyền sở hữu & consent")
        Component(repo, "Repository Layer", "*/repository.py", "Port + SQLAlchemy adapter")
        Component(crypto, "Field Crypto", "core/crypto.py", "Mã hóa/giải mã trường nhạy cảm (AssessmentResult)")
        Component(db, "DB Session", "core/database.py", "AsyncSession; transaction; pool")
        Component(logger, "Structured Logger", "core/logging.py", "structlog JSON; correlation ID; KHÔNG log PII/kết quả nhạy cảm")
    }

    Rel(router, authMw, "Depends")
    Rel(router, consentGuard, "Depends (route dữ liệu hướng nghiệp)")
    Rel(router, rbac, "Depends")
    Rel(assessH, audit, "Mọi đọc kết quả → audit")
    Rel(assessH, crypto, "Mã hóa/giải mã payload")
    Rel(recH, svc, "Yêu cầu gợi ý (+rationale)")
    Rel(authH, svc, "Uses")
    Rel(svc, repo, "Uses (Port)")
    Rel(repo, db, "Uses")
```

---

### Level 3 — Component Diagram — Frontend (Next.js App Router)

```mermaid
C4Component
    title Component Diagram — Frontend (Next.js 16 / React 19)

    Container_Boundary(spa, "Frontend (Next.js)") {
        Component(router, "App Router", "Next.js file routing", "(public) RSC SEO Điều 5a + (app) client; guard vai trò; chặn route [gate] nếu account=pending_guardian_consent")
        Component(authStore, "Auth Store", "Zustand (in-memory)", "access token in-memory (KHÔNG persist/localStorage); refresh httpOnly cookie; auto-refresh")
        Component(apiClient, "API Client", "typed fetch wrapper", "Bearer inject; 401→refresh→retry single-flight; correlation ID")
        Component(queryLayer, "Query Layer", "TanStack Query v5", "Server-state cache; stale-while-revalidate")
        Component(authPages, "Auth + Onboarding", "Login/Register/AgeGate", "Đăng ký → suy ra age_band → cổng giám hộ <16")
        Component(guardianFlow, "Guardian Consent Flow", "GuardianInvite/Consent", "Mời & xác nhận giám hộ; đồng xem")
        Component(assessment, "Assessment UI", "RIASEC/VIPS/MBTI", "Làm test; hiển thị kết quả kèm giải thích (cảnh báo nhạy cảm)")
        Component(careerLib, "Career Library", "CareerList/CareerDetail (RSC)", "Thư viện nghề công khai (anonymous, SEO); lọc theo RIASEC/lĩnh vực")
        Component(progressUI, "Progress Dashboard", "Competency 2-trục", "Biểu đồ tiến bộ K-A-R × dev_phase")
        Component(recoUI, "Recommendation UI", "RecoCard", "Gợi ý + lý do + nút xác nhận (không tự áp dụng)")
        Component(counselorUI, "Counselor Console", "3-tier", "DS học sinh được phân công; ghi phiên tư vấn")
        Component(ds, "Design System", "Tailwind + Radix UI", "WCAG 2.1 AA; theme; responsive 320–2560px")
    }

    Rel(router, authPages, "/login /register")
    Rel(router, guardianFlow, "/guardian (khi <16)")
    Rel(router, assessment, "/assessments (protected + consent)")
    Rel(router, progressUI, "/me/progress")
    Rel(assessment, queryLayer, "useQuery/useMutation")
    Rel(queryLayer, apiClient, "HTTP")
    Rel(apiClient, authStore, "Read/write tokens")
```

---

## Chi tiết kiến trúc Frontend

### Cấu trúc thư mục
```
frontend/
├── src/
│   ├── api/            # Axios client + hàm API (typed)
│   ├── components/     # UI tái sử dụng (design system)
│   ├── features/
│   │   ├── auth/       # Login, Register, AgeGate, AuthGuard
│   │   ├── guardian/   # GuardianInvite, ConsentFlow, ChildLink
│   │   ├── assessment/ # RIASEC, VIPS, MBTI, ResultView
│   │   ├── competency/ # ProgressDashboard (2-trục K-A-R × phase)
│   │   ├── careers/    # CareerList, CareerDetail, Filters
│   │   ├── reco/       # RecommendationCard, ConfirmDialog
│   │   ├── wellbeing/  # Module sức khỏe tinh thần (ABCD NL4)
│   │   └── counseling/ # CounselorConsole, SessionForm
│   ├── hooks/  ├── pages/  ├── store/  ├── types/  ├── lib/
│   └── main.tsx
├── vite.config.ts ├── tailwind.config.ts
├── vitest.config.ts └── playwright.config.ts
```

**Nguyên tắc state:** Server-state (kết quả test, năng lực, nghề, gợi ý) ở TanStack Query; client-state (token, preference UI) ở Zustand. Không trùng lặp. **Kết quả trắc nghiệm nhạy cảm không cache lâu ở client**, không lưu localStorage.

---

## Chi tiết kiến trúc Backend

### Hexagonal (Ports & Adapters)
```
┌───────────────────────────────────────────────────────────┐
│  HTTP Layer (FastAPI)                                       │
│  Request → Validation → Auth → Consent Guard → RBAC → Handler│
└──────────────────────────┬────────────────────────────────┘
                           │ calls
┌──────────────────────────▼────────────────────────────────┐
│  Service Layer (logic thuần Python, không import framework) │
│  AuthService │ ConsentService │ AssessmentService │         │
│  CompetencyService │ CareerService │ RecommendationService │ │
│  CounselingService                                          │
└──────────────────────────┬────────────────────────────────┘
                           │ via Port
┌──────────────────────────▼────────────────────────────────┐
│  Repository Layer (Port — abstract, testable in-memory)     │
│  IUserRepo │ IConsentRepo │ IAssessmentRepo │ ICompetencyRepo│
│  ICareerRepo │ IRecoRepo │ IAuditRepo                        │
└──────────────────────────┬────────────────────────────────┘
                           │ implemented by
┌──────────────────────────▼────────────────────────────────┐
│  SQLAlchemy Adapters — SQLite (MVP) → PostgreSQL            │
│  Trường nhạy cảm đi qua Field Crypto trước khi ghi          │
└───────────────────────────────────────────────────────────┘
```

### Cấu trúc thư mục
```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py  ├── database.py  ├── security.py
│   │   ├── consent.py     # Consent Guard (CP-1/CP-2)
│   │   ├── authz.py       # RBAC quan hệ (CP-4)
│   │   ├── audit.py       # Audit writer (CP-3)
│   │   ├── crypto.py      # Field-level crypto cho dữ liệu nhạy cảm
│   │   ├── logging.py  ├── middleware.py  └── exceptions.py
│   ├── auth/              # User, RefreshToken
│   ├── guardians/         # GuardianLink, GuardianConsent
│   ├── assessments/       # Instrument, Item, Result (sensitive)
│   ├── competency/        # Competency, Indicator, LearnerProgress, LearnerDomainPhase
│   ├── careers/           # CareerProfile, ContentItem, Pathway
│   ├── reco/              # Recommendation (rationale, human-in-the-loop)
│   ├── counseling/        # School, SchoolClass, CounselingSession
│   └── api/v1/router.py
├── migrations/            # Alembic
├── tests/{unit,integration}/  conftest.py
├── tla/                   # Đặc tả TLA+ (xem docs/formal-verification)
├── pyproject.toml └── Dockerfile
```

---

## Thiết kế CSDL

### Sơ đồ thực thể (ERD) — theo spec.md §5

```mermaid
erDiagram
    USER {
        uuid id PK
        string email UK
        string hashed_password
        date date_of_birth
        enum age_band "under_16|16_17|adult"
        enum user_type "student|working"
        enum school_level
        enum account_status "active|pending_guardian_consent|suspended|deleted"
        timestamp created_at
    }
    GUARDIAN_LINK {
        uuid id PK
        uuid child_user_id FK
        uuid guardian_user_id FK
        string relationship
        timestamp verified_at
        enum verification_method "email|vneid"
    }
    GUARDIAN_CONSENT {
        uuid id PK
        uuid child_user_id FK
        uuid guardian_link_id FK
        string scope
        enum status "active|revoked"
        timestamp granted_at
        timestamp revoked_at
    }
    ASSESSMENT_INSTRUMENT {
        uuid id PK
        enum type "riasec|vips|mbti"
        string version
        bool is_active
    }
    ASSESSMENT_RESULT {
        uuid id PK
        uuid user_id FK
        uuid instrument_id FK
        blob result_payload "ENCRYPTED"
        bool is_sensitive "default true"
        int version
        timestamp created_at
    }
    COMPETENCY {
        uuid id PK
        string code "NL1..NL12"
        enum area "A|B|C"
        string name_vi
        array dieu5_codes
    }
    INDICATOR {
        uuid id PK
        uuid competency_id FK
        enum depth "K|A|R"
        text statement_vi
        char dieu5_code
    }
    LEARNER_PROGRESS {
        uuid id PK
        uuid user_id FK
        uuid competency_id FK
        enum depth_achieved "K|A|R"
        timestamp achieved_at
    }
    CAREER_PROFILE {
        uuid id PK
        string name
        array riasec_codes
        text training_paths
        text labor_market_outlook
        char dieu5_code "a"
    }
    RECOMMENDATION {
        uuid id PK
        uuid user_id FK
        json payload
        text rationale "NOT NULL"
        bool requires_human_confirmation
        uuid confirmed_by FK
        enum confirmed_decision "accepted|rejected|deferred"
    }
    COUNSELING_SESSION {
        uuid id PK
        uuid counselor_id FK
        uuid student_id FK
        enum tier "1|2|3"
        text notes
    }
    AUDIT_LOG {
        uuid id PK
        uuid actor_id
        string action
        string target_type
        bool is_sensitive_access
        string correlation_id
        timestamp created_at
    }
    REFRESH_TOKEN {
        uuid id PK
        uuid user_id FK
        string token_hash UK
        timestamp expires_at
        timestamp revoked_at
    }

    USER ||--o{ GUARDIAN_LINK : "child"
    USER ||--o{ GUARDIAN_CONSENT : "consented"
    GUARDIAN_LINK ||--o{ GUARDIAN_CONSENT : "basis"
    USER ||--o{ ASSESSMENT_RESULT : "owns (sensitive)"
    ASSESSMENT_INSTRUMENT ||--o{ ASSESSMENT_RESULT : "produces"
    COMPETENCY ||--o{ INDICATOR : "has K/A/R"
    USER ||--o{ LEARNER_PROGRESS : "progresses"
    COMPETENCY ||--o{ LEARNER_PROGRESS : "tracked"
    USER ||--o{ RECOMMENDATION : "receives"
    USER ||--o{ COUNSELING_SESSION : "student"
    USER ||--o{ REFRESH_TOKEN : "has"
```

### Chiến lược Index

| Bảng | Index | Loại | Lý do |
|------|-------|------|-------|
| user | email | UNIQUE | Login |
| user | age_band, account_status | COMPOSITE | Cổng consent <16 |
| guardian_consent | child_user_id, status | COMPOSITE | Kiểm tra consent active (CP-1, hot path) |
| assessment_result | user_id, instrument_id, version | COMPOSITE | Lấy kết quả mới nhất; versioned |
| learner_progress | user_id, competency_id | COMPOSITE | Bảng tiến bộ K-A-R |
| career_profile | riasec_codes (GIN/JSON) | INDEX | Lọc nghề theo nhóm RIASEC |
| content_item | dieu5_code, competency_id, dev_phase, school_level | COMPOSITE | Phân tầng nội dung |
| recommendation | user_id, confirmed_decision | COMPOSITE | Trạng thái gợi ý |
| audit_log | actor_id, created_at | COMPOSITE | Truy vết |
| refresh_token | token_hash | UNIQUE | Validate token |

> **Lưu ý mã hóa:** `assessment_result.result_payload` mã hóa at-rest (Field Crypto), **không index trên nội dung kết quả** (chỉ index metadata). Truy cập luôn sinh `audit_log` (CP-3).

---

## Chiến lược xử lý lỗi

### Error Response Schema
```json
{
  "error": {
    "code": "GUARDIAN_CONSENT_REQUIRED",
    "message": "Tài khoản dưới 16 tuổi cần đồng ý của người giám hộ trước khi xử lý dữ liệu hướng nghiệp",
    "details": {},
    "request_id": "req_01HX..."
  }
}
```

### Bản đồ HTTP Status

| Code | Khi nào |
|------|---------|
| 200/201/204 | Thành công GET/PATCH / POST / DELETE |
| 400/422 | Lỗi validate (Pydantic) |
| 401 | Thiếu/sai/hết hạn access token |
| 403 | Hợp lệ nhưng không đủ quyền (RBAC), **hoặc thiếu GuardianConsent** (`GUARDIAN_CONSENT_REQUIRED`) |
| 404 | Không tồn tại hoặc không sở hữu |
| 409 | Trùng email khi đăng ký |
| 429 | Vượt rate limit (Retry-After) |
| 451 | (tùy chọn) Không thể xử lý vì lý do pháp lý (consent thu hồi) |
| 500/503 | Lỗi nội bộ (không lộ stack) / DB không sẵn sàng |

---

## Chiến lược Observability

### Định dạng log (NDJSON)
```json
{
  "timestamp": "2026-05-29T10:00:00.000Z",
  "level": "info",
  "service": "weup-api",
  "version": "2.0.0",
  "request_id": "req_01HX...",
  "actor_id": "usr_01HX...",
  "method": "POST",
  "path": "/api/v1/assessments/riasec/submit",
  "status_code": 201,
  "duration_ms": 14,
  "event": "assessment.submitted"
}
```
> ⚠️ **Tuyệt đối không log**: nội dung kết quả trắc nghiệm, payload gợi ý cá nhân, token, PII (NFR-06/NFR-10). Sự kiện nhạy cảm chỉ log *metadata* (loại, thời điểm, actor) + ghi `audit_log` riêng.

### Log levels
| Level | Dùng |
|-------|------|
| DEBUG | Chi tiết query (chỉ dev) |
| INFO | Request in/out; sự kiện nghiệp vụ (consent granted, assessment submitted, reco confirmed) |
| WARNING | Gần rate limit; query chậm (>50ms); consent sắp/đã thu hồi |
| ERROR | Exception; lỗi DB; lỗi audit-write (nghiêm trọng — vi phạm CP-3) |

### Metrics (`/metrics`, Prometheus)
- `http_requests_total{method,path,status}`, `http_request_duration_seconds`
- `sensitive_access_total` (đối chiếu với `audit_writes_total` — phải bằng nhau, giám sát CP-3)
- `guardian_consent_pending_gauge`
- `recommendations_total{decision}` (theo dõi tỉ lệ human confirm)
