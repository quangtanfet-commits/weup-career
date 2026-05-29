"""Careers API integration tests (FR-30..33/40..42/50..51).

Core distinction tested here: the career library + 5c/5d content are **public**
(Điều 5(a)) — Bearer auth only, NOT consent-gated. An under-16 still awaiting
guardian consent (account ``pending_guardian_consent``) can GET /careers and
/content with 200, unlike assessments/progress which return 403.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import child_dob, register_payload

pytestmark = pytest.mark.asyncio


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/register", json=register_payload(**kw))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _adult(client: AsyncClient, email: str = "adult@example.com") -> str:
    await _register(client, email=email, dob="1990-01-01")
    return await _token(client, email)


async def _under16_no_consent(client: AsyncClient) -> str:
    """Register a <16 account that stays in pending_guardian_consent."""
    await _register(
        client, email="kid@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    return await _token(client, "kid@example.com")


# -- GET /careers ----------------------------------------------------------


async def test_list_careers_returns_seeded(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/careers", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == seeded_careers["careers"]
    # Summary view carries RIASEC list + training level + dieu5='a'.
    for c in body:
        assert isinstance(c["riasec_codes"], list)
        assert c["dieu5_code"] == "a"
        assert "training_level" in c


async def test_list_careers_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/careers")).status_code == 401


async def test_filter_careers_by_riasec(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """FR-32: filter careers by RIASEC group (assessment → related careers)."""
    token = await _adult(client)
    resp = await client.get("/api/v1/careers", params={"riasec": "I"}, headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body  # at least one investigative career seeded
    assert all("I" in c["riasec_codes"] for c in body)
    # A letter not present in any seeded career should narrow the set.
    all_resp = await client.get("/api/v1/careers", headers=_auth(token))
    assert len(body) <= len(all_resp.json())


async def test_filter_careers_by_field(client: AsyncClient, seeded_careers: dict[str, int]) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/careers", params={"field": "technology"}, headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body and all(c["field"] == "technology" for c in body)


async def test_filter_careers_by_training_level(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get(
        "/api/v1/careers", params={"training_level": "vocational"}, headers=_auth(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body and all(c["training_level"] == "vocational" for c in body)


async def test_filter_careers_by_pathway_gdnn_vocational_secondary(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """FR-31: careers reachable via the GDNN / trường-trung-học-nghề branch."""
    token = await _adult(client)
    voc = await client.get(
        "/api/v1/careers",
        params={"pathway_type": "vocational_secondary"},
        headers=_auth(token),
    )
    assert voc.status_code == 200
    assert voc.json()  # the cơ khí career is on this branch

    gdnn = await client.get(
        "/api/v1/careers", params={"pathway_type": "gdnn"}, headers=_auth(token)
    )
    assert gdnn.status_code == 200
    assert gdnn.json()


async def test_filter_careers_no_match_returns_empty(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get(
        "/api/v1/careers", params={"field": "no-such-field"}, headers=_auth(token)
    )
    assert resp.status_code == 200
    assert resp.json() == []


# -- GET /careers/{id} -----------------------------------------------------


async def test_get_career_detail(client: AsyncClient, seeded_careers: dict[str, int]) -> None:
    token = await _adult(client)
    first = (await client.get("/api/v1/careers", headers=_auth(token))).json()[0]
    resp = await client.get(f"/api/v1/careers/{first['id']}", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == first["id"]
    assert isinstance(body["required_competencies"], list)
    assert isinstance(body["pathways"], list)
    assert "training_paths" in body and "labor_market_outlook" in body


async def test_get_career_unknown_404(client: AsyncClient, seeded_careers: dict[str, int]) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/careers/does-not-exist", headers=_auth(token))
    assert resp.status_code == 404


async def test_get_career_requires_auth(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    assert (await client.get("/api/v1/careers/x")).status_code == 401


# -- GET /content ----------------------------------------------------------


async def test_list_content_published_only_by_default(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/content", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body
    assert all(item["status"] == "published" for item in body)


async def test_list_content_filter_by_dieu5(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/content", params={"dieu5_code": "c"}, headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body and all(item["dieu5_code"] == "c" for item in body)


async def test_list_content_filter_by_competency(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get(
        "/api/v1/content", params={"competency_code": "NL10"}, headers=_auth(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body and all(item["competency_code"] == "NL10" for item in body)


async def test_list_content_filter_by_dev_phase_and_level(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get(
        "/api/v1/content",
        params={"dev_phase": "exploration", "school_level": "lower_secondary"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body
    assert all(
        item["dev_phase"] == "exploration" and item["school_level"] == "lower_secondary"
        for item in body
    )


async def test_list_content_can_request_drafts(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/content", params={"status": "draft"}, headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body and all(item["status"] == "draft" for item in body)


async def test_list_content_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/content")).status_code == 401


# -- PUBLIC, NOT consent-gated (the core slice-4 distinction) --------------


async def test_under16_without_consent_can_list_careers_200(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    """Điều 5(a) public: a <16 awaiting consent still gets 200 on /careers.

    Contrast with /me/progress and /assessments submit which return 403
    GUARDIAN_CONSENT_REQUIRED for the same account.
    """
    token = await _under16_no_consent(client)
    # Sanity: the same account is blocked from consent-gated career data.
    gated = await client.get("/api/v1/me/progress", headers=_auth(token))
    assert gated.status_code == 403
    assert gated.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"

    # But the public career library is reachable.
    careers = await client.get("/api/v1/careers", headers=_auth(token))
    assert careers.status_code == 200
    assert len(careers.json()) == seeded_careers["careers"]


async def test_under16_without_consent_can_get_career_detail_200(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _under16_no_consent(client)
    listing = await client.get("/api/v1/careers", headers=_auth(token))
    cid = listing.json()[0]["id"]
    detail = await client.get(f"/api/v1/careers/{cid}", headers=_auth(token))
    assert detail.status_code == 200


async def test_under16_without_consent_can_list_content_200(
    client: AsyncClient, seeded_careers: dict[str, int]
) -> None:
    token = await _under16_no_consent(client)
    resp = await client.get("/api/v1/content", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()
