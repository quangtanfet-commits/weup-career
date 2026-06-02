"""Tests for POST /me/progress/dev-phase (G-2, FR-23).

Closes the gap where dev_phase could be inferred/read but not SET via the API:
- a learner can deviate from the school_level-inferred default,
- a working user can hold several phases at once (one per area, non-linear ABCD),
- the write is consent-gated for under-16 (CP-1/CP-2).
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import child_dob, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    return await register_and_verify(client, mailer_of(client), **kw)


async def _token(client: AsyncClient, email: str) -> str:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password123"}
    )
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_set_dev_phase_deviation_reflected_in_progress(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    """An upper_secondary student (default planning) can deviate one area."""
    await _register(
        client, email="dev@example.com", dob="2008-01-01", school_level="upper_secondary"
    )
    tok = await _token(client, "dev@example.com")

    resp = await client.post(
        "/api/v1/me/progress/dev-phase",
        json={"area": "A_personal", "dev_phase": "awareness"},
        headers=_auth(tok),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json() == {"area": "A_personal", "dev_phase": "awareness"}

    prog = (await client.get("/api/v1/me/progress", headers=_auth(tok))).json()
    by_area = {p["area"]: p["dev_phase"] for p in prog}
    # Deviated area shows awareness; other areas keep the inferred default (planning).
    assert by_area["A_personal"] == "awareness"
    assert by_area["B_exploration"] == "planning"


async def test_working_user_holds_multiple_phases(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    """Non-linear ABCD: a working user can be at different phases per area."""
    await _register(client, email="work@example.com", dob="1990-01-01", user_type="working")
    tok = await _token(client, "work@example.com")

    await client.post(
        "/api/v1/me/progress/dev-phase",
        json={"area": "A_personal", "dev_phase": "planning"},
        headers=_auth(tok),
    )
    await client.post(
        "/api/v1/me/progress/dev-phase",
        json={"area": "B_exploration", "dev_phase": "awareness"},
        headers=_auth(tok),
    )

    prog = (await client.get("/api/v1/me/progress", headers=_auth(tok))).json()
    by_area = {p["area"]: p["dev_phase"] for p in prog}
    assert by_area["A_personal"] == "planning"
    assert by_area["B_exploration"] == "awareness"


async def test_latest_set_wins_for_same_area(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    await _register(client, email="re@example.com", dob="1990-01-01")
    tok = await _token(client, "re@example.com")
    await client.post(
        "/api/v1/me/progress/dev-phase",
        json={"area": "C_building", "dev_phase": "awareness"},
        headers=_auth(tok),
    )
    await client.post(
        "/api/v1/me/progress/dev-phase",
        json={"area": "C_building", "dev_phase": "planning"},
        headers=_auth(tok),
    )
    prog = (await client.get("/api/v1/me/progress", headers=_auth(tok))).json()
    by_area = {p["area"]: p["dev_phase"] for p in prog}
    assert by_area["C_building"] == "planning"


async def test_set_dev_phase_requires_guardian_consent_under_16(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    """Under-16 without active consent cannot write dev_phase (CP-1)."""
    await _register(
        client, email="kid@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    tok = await _token(client, "kid@example.com")
    resp = await client.post(
        "/api/v1/me/progress/dev-phase",
        json={"area": "A_personal", "dev_phase": "exploration"},
        headers=_auth(tok),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"
