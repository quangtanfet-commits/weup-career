# State Diagrams

**Version:** 1.0.0 | **Date:** 2026-05-27

---

## Todo Item State Machine

This is the canonical FSM that TLA+ will verify.

```mermaid
stateDiagram-v2
    [*] --> open : create_todo()

    open --> in_progress : start_todo()\n[user owns todo]
    open --> done : complete_todo()\n[user owns todo]
    open --> deleted : delete_todo()\n[user owns todo]
    
    in_progress --> open : reopen_todo()\n[user owns todo]
    in_progress --> done : complete_todo()\n[user owns todo]
    in_progress --> deleted : delete_todo()\n[user owns todo]

    done --> open : reopen_todo()\n[user owns todo]
    done --> deleted : delete_todo()\n[user owns todo]

    deleted --> open : restore_todo()\n[user owns todo, within 30 days]
    deleted --> [*] : permanent_delete()\n[user owns todo]
    deleted --> [*] : purge_job()\n[deleted_at > 30 days ago]
```

### State Invariants

| State | Invariant |
|-------|-----------|
| `open` | `completed_at IS NULL`, `is_deleted = false` |
| `in_progress` | `completed_at IS NULL`, `is_deleted = false` |
| `done` | `completed_at IS NOT NULL`, `is_deleted = false` |
| `deleted` | `is_deleted = true`, `deleted_at IS NOT NULL` |
| `[* terminal]` | Row no longer queryable by any user |

### Valid Transitions Only (Rejected Paths)

- `done → in_progress` is **not allowed** (must reopen first)
- `deleted → done` is **not allowed** (must restore to open first, then complete)
- Any transition by a user who does not own the todo → **403 Forbidden**

---

## Authentication Session State Machine

```mermaid
stateDiagram-v2
    [*] --> anonymous : app_load()

    anonymous --> authenticated : login_success()\nor register_success()

    authenticated --> token_refreshing : access_token_near_expiry()\nor 401_received()
    
    token_refreshing --> authenticated : refresh_success()
    token_refreshing --> anonymous : refresh_failed()\nor refresh_token_revoked()
    
    authenticated --> anonymous : logout()\nor account_deleted()
    authenticated --> anonymous : session_timeout()\n[refresh_token_expired]
```

### Session State Data

| State | access_token | refresh_token (cookie) | user_id |
|-------|-------------|----------------------|---------|
| `anonymous` | null | absent | null |
| `authenticated` | valid JWT string | present (httpOnly) | set |
| `token_refreshing` | expiring JWT (still usable) | present | set |

---

## Refresh Token Lifecycle

```mermaid
stateDiagram-v2
    [*] --> active : issue_refresh_token()

    active --> revoked_by_logout : logout()\n[explicit user action]
    active --> revoked_by_rotation : use_for_refresh()\n[new token issued atomically]
    active --> expired : expires_at < NOW()

    revoked_by_logout --> [*] : purge_job()
    revoked_by_rotation --> [*] : purge_job()
    expired --> [*] : purge_job()
```

**Security property:** A refresh token transitions from `active → revoked_by_rotation` at the same database transaction boundary as a new token moving to `active`. There is never a moment where two valid tokens exist for the same session.

---

## Request Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> received : HTTP request arrives at Nginx

    received --> rate_checked : rate_limiter.check()
    rate_checked --> rejected_429 : limit_exceeded
    rate_checked --> auth_checked : limit_ok

    auth_checked --> rejected_401 : no_token or invalid_token
    auth_checked --> authorized : valid_token

    authorized --> validated : request_body.valid
    authorized --> rejected_422 : request_body.invalid

    validated --> processing : handler.execute()

    processing --> success : db_write_ok\nor db_read_ok
    processing --> failed_500 : unexpected_exception
    processing --> failed_404 : resource_not_found
    processing --> failed_403 : ownership_check_failed

    success --> [*] : response_sent (200/201/204)
    rejected_429 --> [*] : response_sent (429)
    rejected_401 --> [*] : response_sent (401)
    rejected_422 --> [*] : response_sent (422)
    failed_500 --> [*] : response_sent (500, exception_logged)
    failed_404 --> [*] : response_sent (404)
    failed_403 --> [*] : response_sent (403)
```

---

## Frontend Page State Machine

```mermaid
stateDiagram-v2
    [*] --> loading : app_init()

    loading --> login : no_auth_session
    loading --> todos : valid_session_restored

    login --> registering : click_register
    registering --> login : registration_success\nor click_login

    login --> todos : login_success
    
    todos --> creating : click_add_todo
    creating --> todos : save_success\nor cancel

    todos --> editing : click_edit_todo
    editing --> todos : save_success\nor cancel\nor esc_key

    todos --> tag_management : click_manage_tags
    tag_management --> todos : close

    todos --> login : logout\nor session_expired
```

---

## Optimistic Update Conflict Resolution

```mermaid
stateDiagram-v2
    [*] --> idle

    idle --> optimistic_applied : mutate_action()\n[instant local update]
    
    optimistic_applied --> committed : server_success()\n[replace temp with real data]
    optimistic_applied --> rolled_back : server_error()\n[restore snapshot]

    committed --> idle : cache_invalidated()
    rolled_back --> idle : error_toast_shown()
```
