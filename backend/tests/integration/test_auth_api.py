"""Auth API integration tests (FR-01/02/05/06, CP-7)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import child_dob, register_payload

pytestmark = pytest.mark.asyncio


async def test_health_and_ready(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/health")).status_code == 200
    ready = await client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "up"


async def test_register_adult_active(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/register", json=register_payload())
    assert resp.status_code == 201
    body = resp.json()
    assert body["account_status"] == "active"
    assert body["age_band"] == "adult"
    assert "hashed_password" not in body


async def test_register_under16_pending_consent_cp1(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            email="kid@example.com", dob=child_dob(12), school_level="lower_secondary"
        ),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["age_band"] == "under_16"
    assert body["account_status"] == "pending_guardian_consent"


async def test_register_duplicate_email_409(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=register_payload())
    resp = await client.post("/api/v1/auth/register", json=register_payload())
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "CONFLICT"


async def test_register_email_normalized(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/register", json=register_payload(email="  MixEd@Example.COM ")
    )
    assert resp.json()["email"] == "mixed@example.com"


@pytest.mark.parametrize(
    "password",
    ["short1A", "alllower123", "ALLUPPER123", "NoDigitsHere"],
)
async def test_register_weak_password_422(client: AsyncClient, password: str) -> None:
    resp = await client.post("/api/v1/auth/register", json=register_payload(password=password))
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_register_future_dob_422(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/register", json=register_payload(dob="2999-01-01"))
    assert resp.status_code == 422


async def test_login_success_sets_cookie(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=register_payload())
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 15 * 60
    assert "refresh_token" in resp.cookies


async def test_login_wrong_password_401(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=register_payload())
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "WrongPass1"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_login_unknown_email_401(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "Password123"},
    )
    assert resp.status_code == 401


async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


async def test_me_returns_profile(client: AsyncClient) -> None:
    await client.post("/api/v1/auth/register", json=register_payload())
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    token = login.json()["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "adult@example.com"


async def test_me_bad_token_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401


async def _register_login(client: AsyncClient) -> str:
    await client.post("/api/v1/auth/register", json=register_payload())
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    return login.json()["access_token"]


async def test_refresh_rotates_token(client: AsyncClient) -> None:
    await _register_login(client)
    first = client.cookies.get("refresh_token")
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    rotated = resp.cookies.get("refresh_token")
    assert rotated is not None and rotated != first


async def test_refresh_without_cookie_401(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def _refresh_with(client: AsyncClient, raw: str) -> int:
    # Reset the jar to exactly one refresh cookie — deterministic, no path
    # ambiguity in the test client.
    client.cookies.clear()
    client.cookies.set("refresh_token", raw, domain="test", path="/api/v1/auth")
    resp = await client.post("/api/v1/auth/refresh")
    return resp.status_code


async def test_revoked_refresh_token_reuse_401_cp7(client: AsyncClient) -> None:
    """CP-7: an old (rotated) refresh token cannot mint a new access token."""
    await _register_login(client)
    old_cookie = client.cookies.get("refresh_token")
    assert old_cookie is not None
    # Rotate once — old_cookie is now revoked.
    await client.post("/api/v1/auth/refresh")
    # Present the OLD token explicitly.
    assert await _refresh_with(client, old_cookie) == 401


async def test_reuse_detection_revokes_family_cp7(client: AsyncClient) -> None:
    """Reusing a rotated token revokes the whole family (current one too)."""
    await _register_login(client)
    old_cookie = client.cookies.get("refresh_token")
    await client.post("/api/v1/auth/refresh")
    current_cookie = client.cookies.get("refresh_token")
    assert old_cookie is not None and current_cookie is not None
    # Reuse the OLD revoked token → triggers family revocation.
    assert await _refresh_with(client, old_cookie) == 401
    # Now even the previously-valid current token must be dead.
    assert await _refresh_with(client, current_cookie) == 401


async def test_logout_revokes_refresh(client: AsyncClient) -> None:
    token = await _register_login(client)
    logout = await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 204
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_logout_requires_auth(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/auth/logout")).status_code == 401


async def test_correlation_id_echoed(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health", headers={"X-Request-ID": "req_custom_123"})
    assert resp.headers["X-Request-ID"] == "req_custom_123"
