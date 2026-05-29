# Sơ đồ Trạng thái (State Diagrams) — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29

> Các FSM dưới đây là canonical cho TLA+ (xem [`docs/formal-verification/tla-spec-design.md`](../formal-verification/tla-spec-design.md)). Mỗi FSM gắn với thuộc tính đúng đắn (CP) trong [`docs/spec.md`](../spec.md) §8.

---

## ⭐ GuardianConsent State Machine (CP-1, CP-2) — bất biến pháp lý

FSM kiểm soát việc trẻ <16 có được xử lý dữ liệu hướng nghiệp hay không.

```mermaid
stateDiagram-v2
    [*] --> none : trẻ <16 đăng ký
    none --> invited : invite_guardian()
    invited --> active : guardian_verify_and_consent()
    active --> revoked : guardian_revoke()
    revoked --> active : guardian_consent_again()
    active --> [*] : child_account_deleted()
    revoked --> [*] : child_account_deleted()

    note right of active
        CHỈ ở trạng thái active mới
        cho phép ProcessCareerData()
        (trắc nghiệm / gợi ý). CP-1.
    end note
    note right of revoked
        Dừng mọi xử lý MỚI cho tới khi
        active trở lại. CP-2.
    end note
```

| Trạng thái consent | account_status tương ứng | Xử lý dữ liệu hướng nghiệp? |
|---|---|---|
| `none` / `invited` / `revoked` | `pending_guardian_consent` | ⛔ Không |
| `active` | `active` | ✅ Có |
| (≥16 không cần consent) | `active` | ✅ Có |

---

## Account Status State Machine

```mermaid
stateDiagram-v2
    [*] --> pending_guardian_consent : register() [age_band=under_16]
    [*] --> active : register() [age_band≥16]
    pending_guardian_consent --> active : guardian_consent_active()
    active --> pending_guardian_consent : guardian_consent_revoked()
    active --> suspended : admin_suspend()
    suspended --> active : admin_reinstate()
    active --> deleted : request_deletion()
    pending_guardian_consent --> deleted : request_deletion()
    deleted --> [*] : purge_after_recovery_window()
```

---

## ⭐ Recommendation State Machine (CP-5, CP-6) — human-in-the-loop

```mermaid
stateDiagram-v2
    [*] --> proposed : create_recommendation()\n[rationale ≠ "" — CP-6]
    proposed --> accepted : human_confirm("accepted")\n[confirmed_by ∈ Users]
    proposed --> rejected : human_confirm("rejected")
    proposed --> deferred : human_confirm("deferred")
    accepted --> [*] : applied_to_pathway()
    rejected --> [*]
    deferred --> proposed : re-surface()

    note right of proposed
        Hệ thống KHÔNG tự chuyển khỏi proposed.
        Chỉ con người (student/guardian/counselor)
        mới xác nhận. CP-5.
    end note
```

| Trạng thái | rationale | confirmed_by | Có hiệu lực phân luồng? |
|---|---|---|---|
| `proposed` | bắt buộc ≠ rỗng | NONE | Không |
| `accepted` | ≠ rỗng | người dùng | Có (sau khi người chấp nhận) |
| `rejected`/`deferred` | ≠ rỗng | người dùng | Không |

---

## ⭐ Competency Depth Progression (CP-8) — trục độ sâu K-A-R

Một `(learner, competency)` tiến trên trục độ sâu; **không lùi**, lịch sử append-only.

```mermaid
stateDiagram-v2
    [*] --> none
    none --> K : achieve_indicator(K)\n"Nhận biết"
    K --> A : achieve_indicator(A)\n"Thực hiện/Vận dụng"
    A --> R : achieve_indicator(R)\n"Phản tư"
    R --> R : tiếp tục củng cố

    note right of R
        DepthRank chỉ tăng (K<A<R).
        Lịch sử LearnerProgress giữ nguyên,
        không ghi đè. CP-8.
    end note
```

> Trục này **trực giao** với trục giai đoạn phát triển (Awareness→Exploration→Planning) — xem [`career-frameworks-synthesis.md`](../research/career-frameworks-synthesis.md) §3.

---

## Authentication Session State Machine

```mermaid
stateDiagram-v2
    [*] --> anonymous : app_load()
    anonymous --> authenticated : login_success() / register_success()
    authenticated --> token_refreshing : access_token_near_expiry() / 401_received()
    token_refreshing --> authenticated : refresh_success()
    token_refreshing --> anonymous : refresh_failed() / refresh_token_revoked()
    authenticated --> anonymous : logout() / account_deleted() / session_timeout()
```

| State | access_token | refresh_token (cookie) | actor_id |
|-------|-------------|----------------------|---------|
| `anonymous` | null | absent | null |
| `authenticated` | valid JWT | present (httpOnly) | set |
| `token_refreshing` | expiring JWT (vẫn dùng được) | present | set |

> Khi `authenticated` nhưng `account_status = pending_guardian_consent`, frontend chỉ cho phép luồng giám hộ.

---

## Refresh Token Lifecycle (CP-7)

```mermaid
stateDiagram-v2
    [*] --> active : issue_refresh_token()
    active --> revoked_by_logout : logout()
    active --> revoked_by_rotation : use_for_refresh()\n[token mới phát hành nguyên tử]
    active --> expired : expires_at < NOW()
    revoked_by_logout --> [*] : purge_job()
    revoked_by_rotation --> [*] : purge_job()
    expired --> [*] : purge_job()
```

**Thuộc tính an toàn (CP-7):** chuyển `active → revoked_by_rotation` xảy ra cùng ranh giới giao dịch với token mới thành `active`. Không bao giờ tồn tại hai token active cho cùng phiên.

---

## Request Lifecycle State Machine (thêm cổng consent)

```mermaid
stateDiagram-v2
    [*] --> received : request tới Nginx
    received --> rate_checked : rate_limiter.check()
    rate_checked --> rejected_429 : limit_exceeded
    rate_checked --> auth_checked : limit_ok
    auth_checked --> rejected_401 : no/invalid token
    auth_checked --> consent_checked : valid token
    consent_checked --> rejected_403_consent : <16 && no active consent (CP-1)
    consent_checked --> authorized : consent OK / không cần
    authorized --> rejected_403_rbac : RBAC fail (CP-4)
    authorized --> validated : body valid
    authorized --> rejected_422 : body invalid
    validated --> processing : handler.execute()
    processing --> success : ok
    processing --> failed_404 : not_found
    processing --> failed_500 : exception
    success --> [*] : 200/201/204
    rejected_429 --> [*] : 429
    rejected_401 --> [*] : 401
    rejected_403_consent --> [*] : 403 GUARDIAN_CONSENT_REQUIRED
    rejected_403_rbac --> [*] : 403
    rejected_422 --> [*] : 422
    failed_404 --> [*] : 404
    failed_500 --> [*] : 500 (logged, no stack)
```

---

## Frontend Page State Machine

```mermaid
stateDiagram-v2
    [*] --> loading : app_init()
    loading --> login : no_auth_session
    loading --> guardian_gate : session && account=pending_guardian_consent
    loading --> dashboard : session && account=active
    login --> registering : click_register
    registering --> guardian_gate : register [<16]
    registering --> dashboard : register [≥16]
    login --> dashboard : login_success [active]
    guardian_gate --> dashboard : consent_active()
    dashboard --> assessment : open_assessment [consent OK]
    assessment --> dashboard : submit / cancel
    dashboard --> career_library : browse_careers
    dashboard --> recommendations : view_reco
    recommendations --> dashboard : confirm_decision
    dashboard --> login : logout / session_expired
```

---

## Optimistic Update Conflict Resolution (UI)

```mermaid
stateDiagram-v2
    [*] --> idle
    idle --> optimistic_applied : mutate_action()
    optimistic_applied --> committed : server_success()
    optimistic_applied --> rolled_back : server_error()
    committed --> idle : cache_invalidated()
    rolled_back --> idle : error_toast_shown()
```

> ⚠️ Không áp dụng optimistic update cho **gợi ý phân luồng** — gợi ý chỉ hiển thị sau khi server tạo (kèm rationale) và chỉ có hiệu lực sau xác nhận của người (CP-5).
