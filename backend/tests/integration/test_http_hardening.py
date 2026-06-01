"""Integration tests: security headers (PT-05/PT-07) and rate limiting (PT-03).

Headers are asserted via the standard rate-limit-disabled ``client`` fixture
(they apply on every response regardless). Rate-limit behaviour builds dedicated
apps with the limiter enabled and low limits so 429s are deterministic.

See ``docs/security/http-hardening.md``.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from app.core.database import Database
from app.main import create_app
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from tests.conftest import make_settings

pytestmark = pytest.mark.asyncio

_LOGIN = {"email": "nobody@example.com", "password": "Wrongpass123"}


@asynccontextmanager
async def _client(
    settings: object, db: Database, *, addr: tuple[str, int] = ("127.0.0.1", 9)
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(settings)  # type: ignore[arg-type]
    app.state.db = db
    transport = ASGITransport(app=app, client=addr)
    async with LifespanManager(app):
        app.state.db = db
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


# -- security headers -----------------------------------------------------


async def test_headers_present_on_success(client: AsyncClient) -> None:
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "no-referrer"
    assert r.headers["Server"] == "WeUp"
    assert "default-src 'none'" in r.headers["Content-Security-Policy"]
    # HSTS is production-only; test env must not emit it.
    assert "Strict-Transport-Security" not in r.headers


async def test_headers_present_on_error_response(client: AsyncClient) -> None:
    # Unauthenticated /me → 401, but hardening headers must still be stamped.
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Server"] == "WeUp"
    assert "Content-Security-Policy" in r.headers


async def test_csp_exempt_on_docs_but_other_headers_present(
    client: AsyncClient,
) -> None:
    r = await client.get("/api/v1/docs")
    assert r.status_code == 200
    assert "Content-Security-Policy" not in r.headers
    # Non-CSP headers still apply to the docs route.
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Server"] == "WeUp"


async def test_hsts_emitted_in_production(db: Database) -> None:
    s = make_settings(environment="production")
    async with _client(s, db) as c:
        r = await c.get("/api/v1/health")
        assert r.status_code == 200
        assert r.headers["Strict-Transport-Security"] == ("max-age=63072000; includeSubDomains")


# -- rate limiting --------------------------------------------------------


async def test_login_bucket_returns_429_with_envelope_and_retry_after(
    db: Database,
) -> None:
    s = make_settings(
        rate_limit_enabled=True, rate_limit_login_max=2, rate_limit_login_window_seconds=60
    )
    async with _client(s, db) as c:
        for _ in range(2):
            r = await c.post("/api/v1/auth/login", json=_LOGIN)
            assert r.status_code != 429
        blocked = await c.post("/api/v1/auth/login", json=_LOGIN)
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"].isdigit()
    body = blocked.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert isinstance(body["error"]["details"]["retry_after"], int)
    assert body["error"]["request_id"]
    # Hardening headers ride on the 429 too (outermost middleware).
    assert blocked.headers["X-Content-Type-Options"] == "nosniff"


async def test_rate_limit_isolated_per_ip(db: Database) -> None:
    s = make_settings(rate_limit_enabled=True, rate_limit_login_max=2)
    app = create_app(s)
    app.state.db = db
    async with LifespanManager(app):
        app.state.db = db
        t1 = ASGITransport(app=app, client=("10.0.0.1", 1))
        t2 = ASGITransport(app=app, client=("10.0.0.2", 2))
        async with (
            AsyncClient(transport=t1, base_url="http://test") as c1,
            AsyncClient(transport=t2, base_url="http://test") as c2,
        ):
            for _ in range(2):
                await c1.post("/api/v1/auth/login", json=_LOGIN)
            exhausted = await c1.post("/api/v1/auth/login", json=_LOGIN)
            other_ip = await c2.post("/api/v1/auth/login", json=_LOGIN)
    assert exhausted.status_code == 429
    assert other_ip.status_code != 429


async def test_scopes_independent_login_exhaustion_does_not_block_global(
    db: Database,
) -> None:
    s = make_settings(
        rate_limit_enabled=True,
        rate_limit_login_max=1,
        rate_limit_api_max=1000,
    )
    async with _client(s, db) as c:
        await c.post("/api/v1/auth/login", json=_LOGIN)
        login_blocked = await c.post("/api/v1/auth/login", json=_LOGIN)
        # The global 'api' bucket is a separate counter — health still serves.
        health = await c.get("/api/v1/health")
    assert login_blocked.status_code == 429
    assert health.status_code == 200


async def test_non_api_path_is_never_rate_limited(db: Database) -> None:
    # Limiter enabled with a limit of 1, but a non-/api/v1 path bypasses it.
    s = make_settings(rate_limit_enabled=True, rate_limit_api_max=1)
    async with _client(s, db) as c:
        for _ in range(5):
            r = await c.get("/")
        # 404 (no such route) but crucially never 429 — the limiter skipped it.
        assert r.status_code != 429


async def test_rate_limit_disabled_by_default_in_tests(client: AsyncClient) -> None:
    # The default fixture disables the limiter; many requests never 429.
    for _ in range(25):
        r = await client.post("/api/v1/auth/login", json=_LOGIN)
        assert r.status_code != 429
