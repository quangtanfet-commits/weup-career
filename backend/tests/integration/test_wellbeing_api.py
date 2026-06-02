"""Wellbeing API tests (slice 7, FR-70/FR-71, NG-03).

FR-70: wellbeing content (NL4, dieu5_code='b') is seeded and surfaces through
the existing public ``GET /content`` filter.
FR-71: a student's ``POST /wellbeing/support-request`` creates a Tier-3 referral
routed to a counselor in the student's school; if no counselor exists it is
recorded unrouted. By construction there is NO diagnosis, risk score, or
clinical field anywhere in the model or response (NG-03). The request is audited.
"""

from __future__ import annotations

import pytest
from app.core.audit_models import AuditLog
from app.core.database import Database
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import child_dob, enroll_membership, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio

# Any clinical/risk field name that MUST NOT appear in the API surface (NG-03).
_FORBIDDEN_FIELDS = (
    "diagnosis",
    "risk",
    "risk_score",
    "severity",
    "score",
    "clinical",
    "symptom",
)


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    # ``register_and_verify`` returns the login TokenResponse (``access_token`` +
    # ``user``); these helpers only need the user record (``id``), so unwrap.
    return (await register_and_verify(client, mailer_of(client), **kw))["user"]


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _student_with_consent(client: AsyncClient, *, email: str, parent_email: str) -> str:
    """Register an under-16 student with active guardian consent; return user id."""
    child = await _register(client, email=email, dob=child_dob(13), school_level="lower_secondary")
    await _register(client, email=parent_email, dob="1980-01-01")
    child_token = await _token(client, email)
    guardian_token = await _token(client, parent_email)
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": parent_email, "relationship": "mother"},
        headers=_auth(child_token),
    )
    await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": invite.json()["id"]},
        headers=_auth(guardian_token),
    )
    return child["id"]


# -- FR-70: wellbeing content surfaces through GET /content ---------------


async def test_wellbeing_content_seeded_and_queryable(
    client: AsyncClient, seeded_wellbeing: dict[str, int]
) -> None:
    """NL4 / [TOKEN_e1f8b3d9c4a26057] content is queryable via the public content filter."""
    await _register(client, email="reader@example.com", dob="1990-01-01")
    token = await _token(client, "reader@example.com")

    resp = await client.get(
        "/api/v1/content",
        params={"dieu5_code": "b", "competency_code": "NL4"},
        headers=_auth(token),
    )
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) >= 1
    for item in items:
        assert item["dieu5_code"] == "b"
        assert item["competency_code"] == "NL4"
        assert item["status"] == "published"


# -- FR-71: safe pathway to counselor -------------------------------------


async def test_support_request_routed_to_same_school_counselor(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    counselor = await _register(client, email="wb-couns@example.com", dob="1985-01-01")
    await enroll_membership(db, user_id=counselor["id"], school_id=school, role="counselor")

    student_id = await _student_with_consent(
        client, email="wb-stu@example.com", parent_email="wb-par@example.com"
    )
    await enroll_membership(db, user_id=student_id, school_id=school, role="student")

    student_token = await _token(client, "wb-stu@example.com")
    resp = await client.post(
        "/api/v1/wellbeing/support-request",
        json={"message": "Em muốn được hỗ trợ."},
        headers=_auth(student_token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["student_id"] == student_id
    assert body["counselor_id"] == counselor["id"]  # routed to same-school counselor
    assert body["tier"] == "3"
    assert body["status"] == "open"

    # NG-03: no clinical/risk fields anywhere in the response.
    raw = resp.text.lower()
    for forbidden in _FORBIDDEN_FIELDS:
        assert forbidden not in raw, f"forbidden field {forbidden!r} leaked"

    # Audited.
    async with db.session_factory() as s:
        rows = (
            (
                await s.execute(
                    select(AuditLog).where(AuditLog.action == "wellbeing.support_request.created")
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert rows[0].is_sensitive_access is False  # routing record, not sensitive read


async def test_support_request_recorded_unrouted_when_no_counselor(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """No counselor in the student's school → request still recorded, unrouted."""
    school = seeded_school["school"]
    student_id = await _student_with_consent(
        client, email="lonely@example.com", parent_email="lp@example.com"
    )
    await enroll_membership(db, user_id=student_id, school_id=school, role="student")
    token = await _token(client, "lonely@example.com")
    resp = await client.post(
        "/api/v1/wellbeing/support-request",
        json={"message": "Cần hỗ trợ"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["counselor_id"] is None
    assert resp.json()["status"] == "open"


async def test_support_request_recorded_when_no_school(client: AsyncClient, db: Database) -> None:
    """A ≥16 student with no school membership still gets a recorded request."""
    await _register(client, email="noschool@example.com", dob="2000-01-01")
    token = await _token(client, "noschool@example.com")
    resp = await client.post(
        "/api/v1/wellbeing/support-request",
        json={"message": "x"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["counselor_id"] is None


async def test_under16_without_consent_blocked(client: AsyncClient) -> None:
    """An under-16 without active consent cannot create a request (consent gate)."""
    await _register(
        client, email="nc-child@example.com", dob=child_dob(13), school_level="lower_secondary"
    )
    token = await _token(client, "nc-child@example.com")
    resp = await client.post(
        "/api/v1/wellbeing/support-request",
        json={"message": "x"},
        headers=_auth(token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"


async def test_support_request_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/wellbeing/support-request", json={"message": "x"})
    assert resp.status_code == 401


async def test_student_lists_own_requests(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    student_id = await _student_with_consent(
        client, email="lister@example.com", parent_email="lpar@example.com"
    )
    await enroll_membership(db, user_id=student_id, school_id=school, role="student")
    token = await _token(client, "lister@example.com")
    await client.post(
        "/api/v1/wellbeing/support-request",
        json={"message": "một"},
        headers=_auth(token),
    )
    resp = await client.get("/api/v1/wellbeing/support-requests", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    items = resp.json()
    assert len(items) == 1
    assert items[0]["student_id"] == student_id
    raw = resp.text.lower()
    for forbidden in _FORBIDDEN_FIELDS:
        assert forbidden not in raw


async def test_list_requests_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/wellbeing/support-requests")
    assert resp.status_code == 401
