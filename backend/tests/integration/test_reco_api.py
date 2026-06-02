"""Recommendations API integration tests (FR-60..63, CP-1/CP-4/CP-5/CP-6).

Exercises the real app + in-memory SQLite through the HTTP boundary, reusing the
slice-1 auth/consent and slice-2 assessment flows.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import child_dob, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio

_RIASEC_ANSWERS = {"I_1": 5, "I_2": 5, "R_1": 4, "A_1": 1, "S_1": 1, "E_1": 1, "C_1": 1}


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    # ``register_and_verify`` returns the login TokenResponse (``access_token`` +
    # ``user``); these helpers only need the user record (``id``), so unwrap.
    return (await register_and_verify(client, mailer_of(client), **kw))["user"]


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _adult(client: AsyncClient, email: str = "adult@example.com") -> str:
    await _register(client, email=email, dob="1990-01-01")
    return await _token(client, email)


async def _submit_riasec(client: AsyncClient, token: str) -> None:
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _RIASEC_ANSWERS},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text


async def _child_with_consent(client: AsyncClient) -> tuple[str, str]:
    child = await _register(
        client, email="child@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    await _register(client, email="parent@example.com", dob="1980-01-01")
    child_token = await _token(client, "child@example.com")
    guardian_token = await _token(client, "parent@example.com")
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
    return await _token(client, "child@example.com"), child["id"]


# -- CP-1: consent gate ---------------------------------------------------


async def test_under16_without_consent_403(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """CP-1: generating a recommendation processes career data → 403 without consent."""
    await _register(
        client, email="kid@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    token = await _token(client, "kid@example.com")
    resp = await client.post("/api/v1/recommendations", headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"


async def test_create_requires_auth(client: AsyncClient) -> None:
    assert (await client.post("/api/v1/recommendations")).status_code == 401


async def test_under16_with_consent_can_create(
    client: AsyncClient, seeded_careers: dict[str, int], seeded_instruments: dict[str, str]
) -> None:
    """CP-1: once consent is active, the child can generate a recommendation."""
    token, _ = await _child_with_consent(client)
    await _submit_riasec(client, token)
    resp = await client.post("/api/v1/recommendations", headers=_auth(token))
    assert resp.status_code == 201, resp.text


# -- CP-5 / [CRED_05C18C2F]: shape of a fresh recommendation -----------------------------


async def test_created_recommendation_shape(
    client: AsyncClient, seeded_careers: dict[str, int], seeded_instruments: dict[str, str]
) -> None:
    """CP-5/CP-6: fresh reco needs confirmation, has rationale, no decision yet."""
    token = await _adult(client)
    await _submit_riasec(client, token)
    resp = await client.post("/api/v1/recommendations", headers=_auth(token))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["requires_human_confirmation"] is True  # CP-5: not effective yet
    assert body["confirmed_by"] is None  # system never auto-confirms (CP-5)
    assert body["confirmed_decision"] is None
    assert body["rationale"].strip()  # CP-6: always a rationale
    assert "careers" in body["payload"]
    # Career payload carries explainable per-item rationale.
    for career in body["payload"]["careers"]:
        assert career["rationale"].strip()


async def test_create_without_assessment_still_explains(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """No assessment yet → still a valid, rationale-bearing recommendation (CP-6)."""
    token = await _adult(client)
    resp = await client.post("/api/v1/recommendations", headers=_auth(token))
    assert resp.status_code == 201, resp.text
    assert resp.json()["rationale"].strip()


# -- confirm (CP-5 human-in-the-loop) -------------------------------------


@pytest.mark.parametrize("decision", ["accepted", "rejected", "deferred"])
async def test_confirm_each_decision(
    client: AsyncClient, seeded_careers: dict[str, int], decision: str
) -> None:
    """Only a human confirm makes a reco effective; each decision value works."""
    token = await _adult(client)
    created = await client.post("/api/v1/recommendations", headers=_auth(token))
    reco_id = created.json()["id"]
    resp = await client.post(
        f"/api/v1/recommendations/{reco_id}/confirm",
        json={"decision": decision},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["confirmed_decision"] == decision
    assert body["confirmed_by"] is not None  # the human (owner) confirmed


async def test_confirm_cross_user_404(client: AsyncClient, seeded_careers: dict[str, int]) -> None:
    """CP-4: a user cannot confirm someone else's recommendation (404, not leaked)."""
    owner = await _adult(client, email="owner@example.com")
    created = await client.post("/api/v1/recommendations", headers=_auth(owner))
    reco_id = created.json()["id"]

    other = await _adult(client, email="other@example.com")
    resp = await client.post(
        f"/api/v1/recommendations/{reco_id}/confirm",
        json={"decision": "accepted"},
        headers=_auth(other),
    )
    assert resp.status_code == 404


async def test_confirm_unknown_id_404(client: AsyncClient, seeded_careers: dict[str, int]) -> None:
    token = await _adult(client)
    resp = await client.post(
        "/api/v1/recommendations/does-not-exist/confirm",
        json={"decision": "accepted"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_confirm_invalid_decision_422(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    created = await client.post("/api/v1/recommendations", headers=_auth(token))
    reco_id = created.json()["id"]
    resp = await client.post(
        f"/api/v1/recommendations/{reco_id}/confirm",
        json={"decision": "maybe"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_confirm_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/recommendations/x/confirm", json={"decision": "accepted"})
    assert resp.status_code == 401
