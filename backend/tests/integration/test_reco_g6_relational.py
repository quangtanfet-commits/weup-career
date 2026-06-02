"""G-6: guardian/counselor view + confirm a child's recommendation (CP-4 + CP-5).

A recommendation may be read and confirmed by an authorised human relation —
the owner, a verified guardian, or an assigned counselor — not just the owner.
CP-5 is preserved: ``confirmed_by`` is the ACTUAL confirming person (never the
system), and the rationale (CP-6) is untouched. Cross-relation → 404.
"""

from __future__ import annotations

import pytest
from app.core.database import Database
from httpx import AsyncClient

from tests.conftest import child_dob, enroll_membership, mailer_of, register_and_verify

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


async def _child_with_consent_and_reco(client: AsyncClient) -> tuple[str, str, str, str]:
    """Set up an under-16 child with consent + a recommendation.

    Returns (child_id, child_token, guardian_id, reco_id).
    """
    child = await _register(
        client, email="child@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    guardian = await _register(client, email="parent@example.com", dob="1980-01-01")
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
    child_token = await _token(client, "child@example.com")
    created = await client.post("/api/v1/recommendations", headers=_auth(child_token))
    assert created.status_code == 201, created.text
    return child["id"], child_token, guardian["id"], created.json()["id"]


# -- guardian (CP-5 via guardian) -----------------------------------------


async def test_guardian_can_read_child_reco(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    _, _, _, reco_id = await _child_with_consent_and_reco(client)
    guardian_token = await _token(client, "parent@example.com")
    resp = await client.get(f"/api/v1/recommendations/{reco_id}", headers=_auth(guardian_token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == reco_id


async def test_guardian_can_confirm_child_reco_confirmed_by_is_guardian(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """G-6 + CP-5: guardian confirms; confirmed_by is the guardian's real id."""
    _, _, guardian_id, reco_id = await _child_with_consent_and_reco(client)
    guardian_token = await _token(client, "parent@example.com")
    resp = await client.post(
        f"/api/v1/recommendations/{reco_id}/confirm",
        json={"decision": "accepted"},
        headers=_auth(guardian_token),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["confirmed_decision"] == "accepted"
    assert body["confirmed_by"] == guardian_id  # CP-5: a real human, the guardian
    assert body["rationale"].strip()  # CP-6 untouched


async def test_unrelated_user_cannot_read_or_confirm_404(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """CP-4: an unrelated user gets 404 on read AND confirm (existence-hiding)."""
    _, _, _, reco_id = await _child_with_consent_and_reco(client)
    await _register(client, email="stranger@example.com", dob="1990-01-01")
    token = await _token(client, "stranger@example.com")
    assert (
        await client.get(f"/api/v1/recommendations/{reco_id}", headers=_auth(token))
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/recommendations/{reco_id}/confirm",
            json={"decision": "accepted"},
            headers=_auth(token),
        )
    ).status_code == 404


# -- counselor (CP-5 via counselor, CP-4 scoping) -------------------------


async def test_assigned_counselor_can_confirm_child_reco(
    client: AsyncClient, db: Database, seeded_careers: dict[str, int], seeded_school: dict[str, str]
) -> None:
    """G-6: an assigned counselor confirms; confirmed_by = counselor id (CP-5)."""
    child_id, _, _, reco_id = await _child_with_consent_and_reco(client)
    counselor = await _register(client, email="counselor@example.com", dob="1985-01-01")
    school = seeded_school["school"]
    await enroll_membership(db, user_id=counselor["id"], school_id=school, role="counselor")
    await enroll_membership(db, user_id=child_id, school_id=school, role="student")

    counselor_token = await _token(client, "counselor@example.com")
    resp = await client.post(
        f"/api/v1/recommendations/{reco_id}/confirm",
        json={"decision": "deferred"},
        headers=_auth(counselor_token),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["confirmed_by"] == counselor["id"]
    assert resp.json()["confirmed_decision"] == "deferred"


async def test_counselor_other_school_cannot_confirm_404(
    client: AsyncClient, db: Database, seeded_careers: dict[str, int], seeded_school: dict[str, str]
) -> None:
    """CP-4: a counselor in a different school than the child → 404 on confirm."""
    child_id, _, _, reco_id = await _child_with_consent_and_reco(client)
    counselor = await _register(client, email="counselor@example.com", dob="1985-01-01")
    await enroll_membership(
        db, user_id=counselor["id"], school_id=seeded_school["school"], role="counselor"
    )
    # Child enrolled in a different school.
    await enroll_membership(
        db, user_id=child_id, school_id="00000000-0000-0000-0000-000000000111", role="student"
    )
    counselor_token = await _token(client, "counselor@example.com")
    resp = await client.post(
        f"/api/v1/recommendations/{reco_id}/confirm",
        json={"decision": "accepted"},
        headers=_auth(counselor_token),
    )
    assert resp.status_code == 404
