"""Auth API integration tests (FR-01/02/05/06, CP-7, N-3 email verification)."""

from __future__ import annotations

from urllib.parse import parse_qs, urlsplit

import pytest
from app.core.audit_models import AuditLog
from app.core.database import Database
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import child_dob, mailer_of, register_and_verify, register_payload

pytestmark = pytest.mark.asyncio

_ACCEPTED_MESSAGE = (
    "Nếu thông tin hợp lệ, chúng tôi đã gửi email xác minh. Vui lòng kiểm tra hộp thư."
)


async def _register_verified(client: AsyncClient, **kw: str) -> None:
    """Register (202) → pull token from captured mail → verify (204). No login.

    The seam for tests that need a verified account but want to drive the login
    request themselves (e.g. to assert cookies / token shape / failure codes).
    """
    mailer = mailer_of(client)
    payload = register_payload(**kw)
    email = payload["email"].strip().lower()
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 202, resp.text
    sent = mailer.last_for(email)
    assert sent is not None, f"no verification email captured for {email}"
    token = parse_qs(urlsplit(sent.verify_url).query)["token"][0]
    verify = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify.status_code == 204, verify.text


async def _verification_token_for(client: AsyncClient, email: str) -> str:
    """Most-recent raw verification token captured for ``email`` (N-3 §6.1)."""
    sent = mailer_of(client).last_for(email.strip().lower())
    assert sent is not None, f"no verification email captured for {email}"
    return parse_qs(urlsplit(sent.verify_url).query)["token"][0]


async def test_health_and_ready(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/health")).status_code == 200
    ready = await client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["database"] == "up"


# -- N-3: register is enumeration-safe (always 202, no session) -----------


async def test_register_returns_generic_202_no_session(client: AsyncClient) -> None:
    """N-3 §2.1/§5: register never returns account data or a session — only a
    constant 202 body. No UserOut field, no refresh cookie, no access token."""
    resp = await client.post("/api/v1/auth/register", json=register_payload())
    assert resp.status_code == 202
    body = resp.json()
    assert body == {"message": _ACCEPTED_MESSAGE}
    # None of the leaked-shape fields are present.
    for leaked in ("id", "account_status", "age_band", "access_token", "hashed_password"):
        assert leaked not in body
    assert "refresh_token" not in resp.cookies


async def test_register_adult_active(client: AsyncClient) -> None:
    """The derived account is adult/active — observed post-verify via /me."""
    login = await register_and_verify(client, mailer_of(client))
    token = login["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["account_status"] == "active"
    assert body["age_band"] == "adult"
    assert "hashed_password" not in body


async def test_register_under16_pending_consent_cp1(client: AsyncClient) -> None:
    login = await register_and_verify(
        client,
        mailer_of(client),
        email="kid@example.com",
        dob=child_dob(12),
        school_level="lower_secondary",
    )
    token = login["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["age_band"] == "under_16"
    assert body["account_status"] == "pending_guardian_consent"


async def test_register_duplicate_email_indistinguishable_pt04(client: AsyncClient) -> None:
    """PT-04: a duplicate email must not be a user-enumeration oracle.

    Registration is enumeration-safe: every call returns the SAME 202 + generic
    body whether the email is brand-new or already taken. Neither the status
    code nor any field distinguishes the two (spec §2.1/§5).
    """
    first = await client.post("/api/v1/auth/register", json=register_payload())
    assert first.status_code == 202
    second = await client.post("/api/v1/auth/register", json=register_payload())
    assert second.status_code == 202
    # Byte-for-byte identical generic body — nothing leaks "already exists".
    assert first.json() == second.json() == {"message": _ACCEPTED_MESSAGE}


async def test_register_duplicate_under16_indistinguishable_pt04(client: AsyncClient) -> None:
    """A duplicate under-16 email is likewise indistinguishable: same 202 body."""
    payload = register_payload(
        email="kid@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 202
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 202
    assert first.json() == second.json() == {"message": _ACCEPTED_MESSAGE}


async def test_register_duplicate_is_db_noop_pt04(client: AsyncClient) -> None:
    """The duplicate path must not persist or mutate the existing account: the
    second password is never stored, so the original password still logs in and
    the second does not."""
    # First registration through the full verify flow so the account can log in.
    await register_and_verify(client, mailer_of(client), password="Password123")
    # Re-register the same email with a *different* password (202, suppressed).
    resp = await client.post(
        "/api/v1/auth/register",
        json=register_payload(password="DifferentPass456"),
    )
    assert resp.status_code == 202

    # Original password still authenticates → the account was untouched.
    ok = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    assert ok.status_code == 200

    # The duplicate-registration password was never stored (wrong-pw 401 before
    # the verification gate, so this is a clean credential rejection).
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "DifferentPass456"},
    )
    assert bad.status_code == 401


async def test_register_duplicate_audited_defender_side_pt04(
    client: AsyncClient, db: Database
) -> None:
    """The duplicate path is invisible to the attacker but recorded for the
    defender: it logs ``duplicate_suppressed`` (not a second ``succeeded``)."""
    await client.post("/api/v1/auth/register", json=register_payload())
    await client.post("/api/v1/auth/register", json=register_payload())

    async with db.session_factory() as s:
        succeeded = (
            (await s.execute(select(AuditLog).where(AuditLog.action == "auth.register.succeeded")))
            .scalars()
            .all()
        )
        suppressed = (
            (
                await s.execute(
                    select(AuditLog).where(AuditLog.action == "auth.register.duplicate_suppressed")
                )
            )
            .scalars()
            .all()
        )
    # Exactly one real signup, exactly one suppressed duplicate.
    assert len(succeeded) == 1
    assert len(suppressed) == 1


async def test_register_email_normalized(client: AsyncClient) -> None:
    login = await register_and_verify(client, mailer_of(client), email="  MixEd@Example.COM ")
    token = login["access_token"]
    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json()["email"] == "mixed@example.com"


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


# -- N-3: verify-email (single-use, generic-failure) ----------------------


async def test_verify_email_then_login_succeeds(client: AsyncClient) -> None:
    """The golden path: register (202) → verify (204) → login (200)."""
    resp = await client.post("/api/v1/auth/register", json=register_payload())
    assert resp.status_code == 202
    token = await _verification_token_for(client, "adult@example.com")
    verify = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert verify.status_code == 204
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


async def test_login_before_verify_403_email_not_verified(client: AsyncClient) -> None:
    """N-3 login gate: correct password but unverified email → 403 (post-credential,
    not a pre-auth oracle). The code is distinct from wrong-password 401."""
    resp = await client.post("/api/v1/auth/register", json=register_payload())
    assert resp.status_code == 202
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    assert login.status_code == 403
    assert login.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


async def test_verify_email_replay_rejected_single_use(client: AsyncClient) -> None:
    """A verification token is single-use: replaying a consumed token collapses
    to the SAME generic 401 INVALID_TOKEN as any other bad token (spec §5)."""
    await client.post("/api/v1/auth/register", json=register_payload())
    token = await _verification_token_for(client, "adult@example.com")
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": token})
    ).status_code == 204
    replay = await client.post("/api/v1/auth/verify-email", json={"token": token})
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "INVALID_TOKEN"


async def test_verify_email_unknown_token_generic_401(client: AsyncClient) -> None:
    """An unknown token is indistinguishable from a consumed/expired one (§5)."""
    resp = await client.post(
        "/api/v1/auth/verify-email", json={"token": "totally-made-up-token-value"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_TOKEN"


async def test_verify_email_empty_token_422(client: AsyncClient) -> None:
    """An empty token is a request-shape violation (min_length=1), not an oracle."""
    resp = await client.post("/api/v1/auth/verify-email", json={"token": ""})
    assert resp.status_code == 422


# -- N-3: resend-verification (always 202, no oracle) ---------------------


async def test_resend_verification_unknown_email_202(client: AsyncClient) -> None:
    """Resend for an address that does not exist is a silent no-op → 202."""
    resp = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "ghost@example.com"}
    )
    assert resp.status_code == 202
    assert resp.json() == {"message": _ACCEPTED_MESSAGE}
    # No mail is actually sent to a non-existent account.
    assert mailer_of(client).last_for("ghost@example.com") is None


async def test_resend_verification_issues_fresh_usable_token(client: AsyncClient) -> None:
    """For a live, still-unverified account, resend delivers a working token and
    invalidates the prior one (the new token verifies; the old one is dead)."""
    await client.post("/api/v1/auth/register", json=register_payload())
    first_token = await _verification_token_for(client, "adult@example.com")

    resp = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "adult@example.com"}
    )
    assert resp.status_code == 202
    second_token = await _verification_token_for(client, "adult@example.com")
    assert second_token != first_token

    # Old token is now invalidated…
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": first_token})
    ).status_code == 401
    # …and the freshly-issued one verifies.
    assert (
        await client.post("/api/v1/auth/verify-email", json={"token": second_token})
    ).status_code == 204


async def test_resend_verification_already_verified_202_no_mail(client: AsyncClient) -> None:
    """Resend for an already-verified account is a silent no-op → 202, no new mail."""
    await register_and_verify(client, mailer_of(client))
    before = len(mailer_of(client).sent)
    resp = await client.post(
        "/api/v1/auth/resend-verification", json={"email": "adult@example.com"}
    )
    assert resp.status_code == 202
    # No additional verification mail was queued for the verified account.
    assert len(mailer_of(client).sent) == before


# -- login / me -----------------------------------------------------------


async def test_login_success_sets_cookie(client: AsyncClient) -> None:
    await _register_verified(client)
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
    # Wrong password is rejected with 401 INVALID_CREDENTIALS *before* the email
    # gate, so the account need not be verified for this assertion to hold.
    await client.post("/api/v1/auth/register", json=register_payload())
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "WrongPassword1"},
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
    login = await register_and_verify(client, mailer_of(client))
    token = login["access_token"]
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "adult@example.com"


async def test_me_bad_token_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert resp.status_code == 401


async def _register_login(client: AsyncClient) -> str:
    """Register → verify → login; return the access token (N-3-routed)."""
    return (await register_and_verify(client, mailer_of(client)))["access_token"]


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


async def test_logout_denylists_access_token_h01(client: AsyncClient) -> None:
    """H-01: the access token presented at logout is dead immediately after,
    even though it is cryptographically valid until its 15-min exp."""
    token = await _register_login(client)
    auth = {"Authorization": f"Bearer {token}"}
    # Token works before logout.
    assert (await client.get("/api/v1/auth/me", headers=auth)).status_code == 200
    assert (await client.post("/api/v1/auth/logout", headers=auth)).status_code == 204
    # Same token is now rejected (denylisted jti).
    assert (await client.get("/api/v1/auth/me", headers=auth)).status_code == 401


async def test_logout_access_only_denylists_without_refresh_cookie_h01(
    client: AsyncClient,
) -> None:
    """An access-only logout (no refresh cookie) still revokes the bearer."""
    token = await _register_login(client)
    auth = {"Authorization": f"Bearer {token}"}
    client.cookies.clear()  # drop the refresh cookie — access-only logout
    assert (await client.post("/api/v1/auth/logout", headers=auth)).status_code == 204
    assert (await client.get("/api/v1/auth/me", headers=auth)).status_code == 401


async def test_logout_does_not_affect_other_users_h01(client: AsyncClient) -> None:
    """One user's logout must not denylist another user's token (isolation)."""
    token_a = await _register_login(client)
    client.cookies.clear()
    # Second, independent (verified) user.
    await _register_verified(client, email="other@example.com")
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "Password123"},
    )
    token_b = login_b.json()["access_token"]
    # A logs out.
    assert (
        await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token_a}"})
    ).status_code == 204
    # B's token is untouched.
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    ).status_code == 200


async def test_relogin_after_logout_issues_working_token_h01(
    client: AsyncClient,
) -> None:
    """A fresh login after logout yields a new, non-denylisted token."""
    token = await _register_login(client)
    await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    relogin = await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    new_token = relogin.json()["access_token"]
    assert new_token != token
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    ).status_code == 200


async def test_denylisted_token_rejected_on_public_read_h01(client: AsyncClient) -> None:
    """A denylisted token on an ``optional_current_user`` route → 401, per the
    present-but-invalid policy. Anonymous (no header) still reads fine."""
    token = await _register_login(client)
    await client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    # Anonymous public read is allowed.
    assert (await client.get("/api/v1/careers")).status_code == 200
    # But presenting the denylisted token is an explicit auth attempt → 401.
    resp = await client.get("/api/v1/careers", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


# -- H-02 session-version epoch (re-login / password change) ----------------


async def _login(client: AsyncClient, email: str = "adult@example.com") -> str:
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"},
    )
    return resp.json()["access_token"]


async def test_relogin_invalidates_prior_access_token_h02(client: AsyncClient) -> None:
    """H-02: a second login bumps the user's session epoch, so the bare access
    token minted by the first login is below the live ``sv`` and now rejected —
    even though it is cryptographically valid until its 15-min exp."""
    token_a = await _register_login(client)
    auth_a = {"Authorization": f"Bearer {token_a}"}
    assert (await client.get("/api/v1/auth/me", headers=auth_a)).status_code == 200
    # Re-login → new epoch + new token.
    token_b = await _login(client)
    assert token_b != token_a
    # The old token is now stale (sv below current).
    assert (await client.get("/api/v1/auth/me", headers=auth_a)).status_code == 401
    # The fresh token works.
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    ).status_code == 200


async def test_password_change_invalidates_prior_access_token_h02(client: AsyncClient) -> None:
    """Changing the password bumps the epoch, killing every prior access token."""
    token = await _register_login(client)
    auth = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/api/v1/auth/me", headers=auth)).status_code == 200
    resp = await client.post(
        "/api/v1/me/password",
        headers=auth,
        json={"current_password": "Password123", "new_password": "NewPassword456"},
    )
    assert resp.status_code == 204
    # The token that authorised the change is itself now stale.
    assert (await client.get("/api/v1/auth/me", headers=auth)).status_code == 401


async def test_relogin_does_not_affect_other_users_h02(client: AsyncClient) -> None:
    """One user's re-login bumps only their own epoch — isolation across users."""
    token_a = await _register_login(client)
    client.cookies.clear()
    await _register_verified(client, email="other@example.com")
    token_b = await _login(client, email="other@example.com")
    # A re-logs in (bumps A's epoch only).
    await client.post(
        "/api/v1/auth/login",
        json={"email": "adult@example.com", "password": "Password123"},
    )
    # A's first token is stale…
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    ).status_code == 401
    # …but B's token is untouched.
    assert (
        await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})
    ).status_code == 200


async def test_correlation_id_echoed(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health", headers={"X-Request-ID": "req_custom_123"})
    assert resp.headers["X-Request-ID"] == "req_custom_123"
