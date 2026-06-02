"""content_editor versioning API tests (slice 7, FR-90, G-5).

A global content_editor (``User.is_content_editor``) creates ContentItems with
all mandatory tags and publishes new versions; publishing v2 archives v1.
Non-editors are rejected (403). Authority is re-derived from the DB flag, so a
user who is NOT an editor cannot reach these routes even with a valid token.
The public ``GET /content`` shows only the published version (draft + archived
hidden); an archived prior version is still fetchable by id.
"""

from __future__ import annotations

import pytest
from app.core.audit_models import AuditLog
from app.core.database import Database
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import grant_content_editor, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio

_FULL_TAGS = {
    "title": "Hiểu bản thân để chọn nghề",
    "body": "Nội dung mẫu.",
    "competency_code": "NL1",
    "dieu5_code": "c",
    "depth": "K",
    "dev_phase": "exploration",
    "school_level": "lower_secondary",
    "source_ref": "WeUp MVP",
}


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    # ``register_and_verify`` returns the login TokenResponse (``access_token`` +
    # ``user``); these helpers only need the user record (``id``), so unwrap.
    return (await register_and_verify(client, mailer_of(client), **kw))["user"]


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _editor_token(
    client: AsyncClient, db: Database, email: str = "editor@example.com"
) -> str:
    user = await _register(client, email=email, dob="1985-01-01")
    await grant_content_editor(db, user_id=user["id"])
    # Re-login so the JWT carries the content_editor role.
    return await _token(client, email)


# -- POST /content (create with mandatory tags) ---------------------------


async def test_editor_creates_content_with_all_tags(client: AsyncClient, db: Database) -> None:
    token = await _editor_token(client, db)
    resp = await client.post("/api/v1/content", json=_FULL_TAGS, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["version"] == 1
    assert body["status"] == "draft"
    assert body["competency_code"] == "NL1"

    async with db.session_factory() as s:
        rows = (
            (await s.execute(select(AuditLog).where(AuditLog.action == "content.created")))
            .scalars()
            .all()
        )
    assert len(rows) == 1


@pytest.mark.parametrize(
    "missing", ["competency_code", "dieu5_code", "depth", "dev_phase", "school_level"]
)
async def test_create_content_missing_tag_422(
    client: AsyncClient, db: Database, missing: str
) -> None:
    token = await _editor_token(client, db, email=f"ed-{missing}@example.com")
    payload = {k: v for k, v in _FULL_TAGS.items() if k != missing}
    resp = await client.post("/api/v1/content", json=payload, headers=_auth(token))
    assert resp.status_code == 422, resp.text


async def test_create_content_empty_tag_422(client: AsyncClient, db: Database) -> None:
    """An empty (whitespace-stripped) string tag is rejected (422)."""
    token = await _editor_token(client, db, email="ed-empty@example.com")
    payload = {**_FULL_TAGS, "competency_code": ""}
    resp = await client.post("/api/v1/content", json=payload, headers=_auth(token))
    assert resp.status_code == 422, resp.text


async def test_non_editor_cannot_create_403(client: AsyncClient) -> None:
    await _register(client, email="plain-ed@example.com", dob="1990-01-01")
    token = await _token(client, "plain-ed@example.com")
    resp = await client.post("/api/v1/content", json=_FULL_TAGS, headers=_auth(token))
    assert resp.status_code == 403, resp.text


async def test_create_content_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/content", json=_FULL_TAGS)
    assert resp.status_code == 401


# -- POST /content/{id}/versions (publish-supersession) -------------------


async def test_publish_v2_archives_v1_and_listing_shows_v2(
    client: AsyncClient, db: Database
) -> None:
    token = await _editor_token(client, db, email="pubeditor@example.com")
    created = await client.post("/api/v1/content", json=_FULL_TAGS, headers=_auth(token))
    v1_id = created.json()["id"]

    # Publish v1 (draft -> published as a v2 row? No: publish makes a published
    # version from the lineage). First publish creates version 2 published; the
    # draft v1 stays as the base. Then publish again -> v3, archiving v2.
    pub1 = await client.post(f"/api/v1/content/{v1_id}/versions", headers=_auth(token))
    assert pub1.status_code == 201, pub1.text
    v2 = pub1.json()
    assert v2["status"] == "published"
    assert v2["version"] == 2
    v2_id = v2["id"]

    pub2 = await client.post(f"/api/v1/content/{v2_id}/versions", headers=_auth(token))
    assert pub2.status_code == 201, pub2.text
    v3 = pub2.json()
    assert v3["status"] == "published"
    assert v3["version"] == 3
    v3_id = v3["id"]

    # Public listing (published-only) shows ONLY the latest published version.
    listing = await client.get(
        "/api/v1/content", params={"competency_code": "NL1"}, headers=_auth(token)
    )
    listed_ids = [c["id"] for c in listing.json()]
    assert v3_id in listed_ids
    assert v2_id not in listed_ids  # v2 archived
    assert v1_id not in listed_ids  # v1 still draft

    # The archived prior version is still fetchable by id (traceability).
    archived = await client.get(f"/api/v1/content/{v2_id}", headers=_auth(token))
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    # Audit: two version-published rows.
    async with db.session_factory() as s:
        rows = (
            (
                await s.execute(
                    select(AuditLog).where(AuditLog.action == "content.version.published")
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 2


async def test_publish_unknown_content_404(client: AsyncClient, db: Database) -> None:
    token = await _editor_token(client, db, email="ed404@example.com")
    resp = await client.post("/api/v1/content/no-such-id/versions", headers=_auth(token))
    assert resp.status_code == 404


async def test_non_editor_cannot_publish_403(client: AsyncClient, db: Database) -> None:
    token = await _editor_token(client, db, email="realed@example.com")
    created = await client.post("/api/v1/content", json=_FULL_TAGS, headers=_auth(token))
    content_id = created.json()["id"]

    await _register(client, email="intruder@example.com", dob="1990-01-01")
    intruder = await _token(client, "intruder@example.com")
    resp = await client.post(f"/api/v1/content/{content_id}/versions", headers=_auth(intruder))
    assert resp.status_code == 403


async def test_get_content_item_non_editor_403(client: AsyncClient, db: Database) -> None:
    token = await _editor_token(client, db, email="ed-get@example.com")
    created = await client.post("/api/v1/content", json=_FULL_TAGS, headers=_auth(token))
    content_id = created.json()["id"]

    await _register(client, email="peek@example.com", dob="1990-01-01")
    peek = await _token(client, "peek@example.com")
    resp = await client.get(f"/api/v1/content/{content_id}", headers=_auth(peek))
    assert resp.status_code == 403


async def test_get_unknown_content_item_404(client: AsyncClient, db: Database) -> None:
    token = await _editor_token(client, db, email="ed-get2@example.com")
    resp = await client.get("/api/v1/content/no-such-id", headers=_auth(token))
    assert resp.status_code == 404
