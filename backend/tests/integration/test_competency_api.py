"""Competency API integration tests (FR-20..24, CP-1, CP-4, CP-8).

Reuses the slice-1 auth/consent flow against the real app + in-memory SQLite.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import child_dob, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio


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


# -- GET /competencies ----------------------------------------------------


async def test_list_competencies_returns_twelve(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/competencies", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 12
    codes = {c["code"] for c in body}
    assert codes == {f"NL{i}" for i in range(1, 13)}
    # Each competency carries its three indicators with VI depth labels.
    for comp in body:
        assert len(comp["indicators"]) == 3
        labels = {ind["depth_label_vi"] for ind in comp["indicators"]}
        assert labels == {"Nhận biết", "Thực hiện-Vận dụng", "Phản tư"}
        assert isinstance(comp["dieu5_codes"], list) and comp["dieu5_codes"]


async def test_list_competencies_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/competencies")).status_code == 401


# -- GET /me/progress -----------------------------------------------------


async def test_progress_adult_all_competencies_no_depth(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/me/progress", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 12
    assert all(item["depth_achieved"] is None for item in body)
    assert all(item["depth_label_vi"] is None for item in body)


async def test_progress_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/me/progress")).status_code == 401


async def test_progress_under16_without_consent_403(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    """CP-1: under-16 own progress is career data → consent-gated."""
    await _register(
        client, email="kid@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    token = await _token(client, "kid@example.com")
    resp = await client.get("/api/v1/me/progress", headers=_auth(token))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"


async def test_progress_under16_with_consent_shows_inferred_phase(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    child_token, _ = await _child_with_consent(client)
    resp = await client.get("/api/v1/me/progress", headers=_auth(child_token))
    assert resp.status_code == 200
    body = resp.json()
    # THCS student → exploration inferred across all areas.
    assert all(item["dev_phase"] == "exploration" for item in body)


# -- record indicator → progress reflects (FR-22, CP-8) -------------------


async def _first_indicator(client: AsyncClient, token: str, code: str, depth: str) -> str:
    comps = (await client.get("/api/v1/competencies", headers=_auth(token))).json()
    comp = next(c for c in comps if c["code"] == code)
    return next(i["id"] for i in comp["indicators"] if i["depth"] == depth)


async def test_record_indicator_advances_progress(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    token = await _adult(client)
    ind_a = await _first_indicator(client, token, "NL1", "A")
    resp = await client.post(
        "/api/v1/me/progress/indicators",
        json={"indicator_id": ind_a},
        headers=_auth(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["advanced"] is True
    assert body["depth_achieved"] == "A"
    assert body["depth_label_vi"] == "Thực hiện-Vận dụng"

    # /me/progress now shows depth A on NL1.
    progress = (await client.get("/api/v1/me/progress", headers=_auth(token))).json()
    nl1 = next(p for p in progress if p["code"] == "NL1")
    assert nl1["depth_achieved"] == "A"


async def test_record_lower_depth_does_not_regress_cp8(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    token = await _adult(client)
    ind_r = await _first_indicator(client, token, "NL1", "R")
    ind_k = await _first_indicator(client, token, "NL1", "K")

    await client.post(
        "/api/v1/me/progress/indicators", json={"indicator_id": ind_r}, headers=_auth(token)
    )
    # Recording K after R must not regress.
    resp = await client.post(
        "/api/v1/me/progress/indicators", json={"indicator_id": ind_k}, headers=_auth(token)
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["advanced"] is False
    assert body["depth_achieved"] == "R"  # held at the higher depth

    progress = (await client.get("/api/v1/me/progress", headers=_auth(token))).json()
    nl1 = next(p for p in progress if p["code"] == "NL1")
    assert nl1["depth_achieved"] == "R"


async def test_record_unknown_indicator_404(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.post(
        "/api/v1/me/progress/indicators",
        json={"indicator_id": "does-not-exist"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_record_requires_auth(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    resp = await client.post("/api/v1/me/progress/indicators", json={"indicator_id": "x"})
    assert resp.status_code == 401


# -- CP-4 ownership: progress is per-caller --------------------------------


async def test_progress_is_isolated_per_user_cp4(
    client: AsyncClient, seeded_competencies: dict[str, str]
) -> None:
    owner = await _adult(client, "owner@example.com")
    ind_a = await _first_indicator(client, owner, "NL1", "A")
    await client.post(
        "/api/v1/me/progress/indicators", json={"indicator_id": ind_a}, headers=_auth(owner)
    )

    other = await _adult(client, "other@example.com")
    progress = (await client.get("/api/v1/me/progress", headers=_auth(other))).json()
    # The other user sees no depth — owner's progress is not visible (CP-4).
    assert all(p["depth_achieved"] is None for p in progress)
