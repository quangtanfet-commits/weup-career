"""Unit tests for the fixed-window rate limiter (PT-03, ADR-008).

Covers the pure ``RateLimiter`` counter logic and the request-classification /
identity-resolution helpers without HTTP overhead, so the branch behaviour
(allow / [CRED_5F3A6A23] / [CRED_5F3A6A24]-reset / [CRED_5F3A6A25]) is pinned deterministically.
"""

from __future__ import annotations

from app.core.ratelimit import (
    RateLimiter,
    _classify,
    _identity,
    make_rate_limit_middleware,
)
from app.core.security import create_access_token
from starlette.requests import Request

from tests.conftest import make_settings


def _request(
    *,
    path: str = "/api/v1/health",
    method: str = "GET",
    headers: dict[str, str] | None = None,
    client: tuple[str, int] | None = ("1.2.3.4", 5),
) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": raw,
        "client": client,
        "query_string": b"",
        "scheme": "http",
        "server": ("test", 80),
    }
    return Request(scope)


# -- RateLimiter counter --------------------------------------------------


def test_allows_up_to_limit_then_rejects() -> None:
    rl = RateLimiter()
    for _ in range(3):
        allowed, retry = rl.hit("login", "ip:a", limit=3, window=60, now=100.0)
        assert allowed is True
        assert retry == 0
    allowed, retry = rl.hit("login", "ip:a", limit=3, window=60, now=100.0)
    assert allowed is False
    assert retry >= 1


def test_retry_after_counts_down_within_window() -> None:
    rl = RateLimiter()
    rl.hit("login", "ip:a", limit=1, window=60, now=100.0)
    allowed, retry = rl.hit("login", "ip:a", limit=1, window=60, now=130.0)
    assert allowed is False
    # 60s window opened at t=100; at t=130, ~30s remain.
    assert retry == 30


def test_window_resets_after_elapsed() -> None:
    rl = RateLimiter()
    assert rl.hit("login", "ip:a", limit=1, window=60, now=100.0) == (True, 0)
    assert rl.hit("login", "ip:a", limit=1, window=60, now=130.0)[0] is False
    # Past the window → counter resets, request allowed again.
    assert rl.hit("login", "ip:a", limit=1, window=60, now=161.0) == (True, 0)


def test_distinct_identities_have_independent_buckets() -> None:
    rl = RateLimiter()
    assert rl.hit("login", "ip:a", limit=1, window=60, now=100.0)[0] is True
    assert rl.hit("login", "ip:a", limit=1, window=60, now=100.0)[0] is False
    # Different identity, same scope → unaffected.
    assert rl.hit("login", "ip:b", limit=1, window=60, now=100.0)[0] is True


def test_distinct_scopes_have_independent_buckets() -> None:
    rl = RateLimiter()
    assert rl.hit("login", "ip:a", limit=1, window=60, now=100.0)[0] is True
    assert rl.hit("login", "ip:a", limit=1, window=60, now=100.0)[0] is False
    assert rl.hit("api", "ip:a", limit=1, window=60, now=100.0)[0] is True


def test_prune_drops_stale_entries_when_table_grows() -> None:
    rl = RateLimiter()
    # Fill past the prune threshold with entries from an old window.
    rl._buckets = {("api", f"ip:{i}"): (1, 0.0) for i in range(10_001)}
    # A fresh hit at now well past the 1h cutoff triggers a sweep.
    rl.hit("login", "ip:new", limit=5, window=60, now=10_000.0)
    # Stale entries (window_start=0, older than now-3600) are gone.
    assert ("api", "ip:0") not in rl._buckets
    assert ("login", "ip:new") in rl._buckets


# -- _classify ------------------------------------------------------------


def test_classify_non_api_path_is_skipped() -> None:
    assert _classify(_request(path="/", method="GET")) == (None, "")
    assert _classify(_request(path="/metrics", method="GET")) == (None, "")


def test_classify_auth_post_buckets() -> None:
    assert _classify(_request(path="/api/v1/auth/register", method="POST")) == (
        "register",
        "ip",
    )
    assert _classify(_request(path="/api/v1/auth/login", method="POST")) == (
        "login",
        "ip",
    )
    assert _classify(_request(path="/api/v1/auth/refresh", method="POST")) == (
        "refresh",
        "ip",
    )


def test_classify_other_api_is_global_sub_bucket() -> None:
    assert _classify(_request(path="/api/v1/health", method="GET")) == ("api", "sub")
    # A non-auth POST under /api/v1 also lands in the global bucket.
    assert _classify(_request(path="/api/v1/assessments", method="POST")) == (
        "api",
        "sub",
    )
    # GET on an auth path is not one of the IP buckets → global.
    assert _classify(_request(path="/api/v1/auth/me", method="GET")) == ("api", "sub")


# -- _identity ------------------------------------------------------------


def test_identity_ip_mode() -> None:
    s = make_settings()
    assert _identity(_request(client=("9.9.9.9", 1)), "ip", s) == "ip:9.9.9.9"


def test_identity_ip_mode_no_client() -> None:
    s = make_settings()
    assert _identity(_request(client=None), "ip", s) == "ip:unknown"


def test_identity_sub_mode_with_valid_bearer() -> None:
    s = make_settings()
    token = create_access_token(
        settings=s,
        subject="usr_42",
        email="a@b.com",
        user_type="student",
        age_band="under_16",
        account_status="active",
        roles=["student"],
        session_version=1,
    )
    req = _request(headers={"Authorization": f"Bearer {token}"})
    assert _identity(req, "sub", s) == "sub:usr_42"


def test_identity_sub_mode_bad_token_falls_back_to_ip() -> None:
    s = make_settings()
    req = _request(headers={"Authorization": "Bearer not.a.jwt"}, client=("7.7.7.7", 1))
    assert _identity(req, "sub", s) == "ip:7.7.7.7"


def test_identity_sub_mode_no_auth_header_falls_back_to_ip() -> None:
    s = make_settings()
    assert _identity(_request(client=("8.8.8.8", 1)), "sub", s) == "ip:8.8.8.8"


def test_identity_sub_mode_empty_sub_falls_back_to_ip() -> None:
    """A token that decodes but carries a falsy ``sub`` → IP fallback."""
    s = make_settings()
    token = create_access_token(
        settings=s,
        subject="",
        email="a@b.com",
        user_type="student",
        age_band="under_16",
        account_status="active",
        roles=["student"],
        session_version=1,
    )
    req = _request(headers={"Authorization": f"Bearer {token}"}, client=("6.6.6.6", 1))
    assert _identity(req, "sub", s) == "ip:6.6.6.6"


# -- middleware factory binds bucket config -------------------------------


def test_make_middleware_returns_callable() -> None:
    s = make_settings(rate_limit_enabled=True)
    mw = make_rate_limit_middleware(s)
    assert callable(mw)
