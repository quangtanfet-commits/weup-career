"""Guardian-consent API integration tests (CP-1, CP-2, CP-4, self-consent)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import child_dob, register_payload

pytestmark = pytest.mark.asyncio


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/register", json=register_payload(**kw))
    assert resp.status_code == 201
    return resp.json()


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _setup_child_and_guardian(
    client: AsyncClient,
) -> tuple[dict[str, str], str, str]:
    child = await _register(
        client,
        email="child@example.com",
        dob=child_dob(12),
        school_level="lower_secondary",
    )
    await _register(client, email="parent@example.com", dob="1985-01-01")
    child_token = await _token(client, "child@example.com")
    guardian_token = await _token(client, "parent@example.com")
    return child, child_token, guardian_token


async def test_full_consent_flow_activates_child_cp1(client: AsyncClient) -> None:
    child, child_token, guardian_token = await _setup_child_and_guardian(client)

    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    assert invite.status_code == 201
    link_id = invite.json()["id"]
    assert invite.json()["verification_method"] == "email"

    consent = await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": link_id},
        headers=_auth(guardian_token),
    )
    assert consent.status_code == 201
    assert consent.json()["status"] == "active"

    # Child is now active (CP-1 gate opens).
    me = await client.get("/api/v1/auth/me", headers=_auth(child_token))
    assert me.json()["account_status"] == "active"


async def test_self_consent_forbidden(client: AsyncClient) -> None:
    """A child inviting itself as guardian is rejected (ADR-010)."""
    await _register(
        client,
        email="kid@example.com",
        dob=child_dob(12),
        school_level="lower_secondary",
    )
    token = await _token(client, "kid@example.com")
    resp = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "kid@example.com", "relationship": "self"},
        headers=_auth(token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "SELF_CONSENT_FORBIDDEN"


async def test_invite_unknown_guardian_404(client: AsyncClient) -> None:
    await _register(
        client,
        email="kid2@example.com",
        dob=child_dob(12),
        school_level="lower_secondary",
    )
    token = await _token(client, "kid2@example.com")
    resp = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "nobody@example.com", "relationship": "uncle"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_duplicate_invite_409(client: AsyncClient) -> None:
    _, child_token, _ = await _setup_child_and_guardian(client)
    body = {"guardian_email": "parent@example.com", "relationship": "mother"}
    await client.post("/api/v1/guardians/invite", json=body, headers=_auth(child_token))
    resp = await client.post("/api/v1/guardians/invite", json=body, headers=_auth(child_token))
    assert resp.status_code == 409


async def test_consent_on_foreign_link_404_cp4(client: AsyncClient) -> None:
    """A guardian cannot consent on a link they don't own (returns 404, no leak)."""
    _, child_token, guardian_token = await _setup_child_and_guardian(client)
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    link_id = invite.json()["id"]

    # A stranger guardian tries to consent on someone else's link.
    await _register(client, email="stranger@example.com", dob="1980-01-01")
    stranger_token = await _token(client, "stranger@example.com")
    resp = await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": link_id},
        headers=_auth(stranger_token),
    )
    assert resp.status_code == 404


async def test_consent_missing_link_404(client: AsyncClient) -> None:
    await _register(client, email="g@example.com", dob="1980-01-01")
    token = await _token(client, "g@example.com")
    resp = await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": "does-not-exist"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_double_consent_409(client: AsyncClient) -> None:
    _, child_token, guardian_token = await _setup_child_and_guardian(client)
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    link_id = invite.json()["id"]
    await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": link_id},
        headers=_auth(guardian_token),
    )
    resp = await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": link_id},
        headers=_auth(guardian_token),
    )
    assert resp.status_code == 409


async def test_revoke_returns_child_to_pending_cp2(client: AsyncClient) -> None:
    child, child_token, guardian_token = await _setup_child_and_guardian(client)
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": invite.json()["id"]},
        headers=_auth(guardian_token),
    )

    revoke = await client.post(
        "/api/v1/guardians/consent/revoke",
        json={"child_user_id": child["id"]},
        headers=_auth(guardian_token),
    )
    assert revoke.status_code == 204

    me = await client.get("/api/v1/auth/me", headers=_auth(child_token))
    assert me.json()["account_status"] == "pending_guardian_consent"


async def test_revoke_without_active_consent_404(client: AsyncClient) -> None:
    child, child_token, guardian_token = await _setup_child_and_guardian(client)
    await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    resp = await client.post(
        "/api/v1/guardians/consent/revoke",
        json={"child_user_id": child["id"]},
        headers=_auth(guardian_token),
    )
    assert resp.status_code == 404


async def test_revoke_no_link_404(client: AsyncClient) -> None:
    await _register(client, email="g2@example.com", dob="1980-01-01")
    token = await _token(client, "g2@example.com")
    resp = await client.post(
        "/api/v1/guardians/consent/revoke",
        json={"child_user_id": "someone-else"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_guardian_routes_require_auth(client: AsyncClient) -> None:
    assert (
        await client.post(
            "/api/v1/guardians/invite",
            json={"guardian_email": "p@example.com", "relationship": "x"},
        )
    ).status_code == 401
