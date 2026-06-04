"""Counselor competency framework + self-assessment API integration tests.

Spec refs: §3.11 FR-100..103, ADR-016.

Coverage targets:
  - Framework fetch (GET /api/v1/counselor/competencies)
  - Self-assessment create (POST /api/v1/me/counselor/self-assessments)
  - Self-assessment list   (GET  /api/v1/me/counselor/self-assessments)
  - Counselor-only authorisation (non-counselor → 403/404)
  - CP-1 separation negative test: counselor without guardian/consent can CRUD
  - CP-4 unchanged: new endpoints do not widen cross-counselor/student authority
  - Version increment: repeated submissions version monotonically
"""

from __future__ import annotations

import pytest
from app.core.database import Database
from httpx import AsyncClient

from tests.conftest import enroll_membership, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio


# -- helpers ------------------------------------------------------------------


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    return (await register_and_verify(client, mailer_of(client), **kw))["user"]


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _counselor_with_school(
    client: AsyncClient,
    db: Database,
    school_id: str,
    *,
    email: str = "counselor@weup-test.com",
) -> tuple[str, str]:
    """Register a counselor user + a SchoolMembership. Returns (user_id, token)."""
    user = await _register(client, email=email, dob="1985-01-01")
    await enroll_membership(db, user_id=user["id"], school_id=school_id, role="counselor")
    tok = await _token(client, email)
    return user["id"], tok


async def _seed_framework(client: AsyncClient, db: Database) -> None:
    """Ensure the counselor competency framework is seeded in the test DB."""
    from app.counselor_competency.seed import seed_counselor_competencies

    async with db.session_factory() as s:
        await seed_counselor_competencies(s)
        await s.commit()


# -- GET /api/v1/counselor/competencies ---------------------------------------


async def test_counselor_sees_framework(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-100: authorised counselor can fetch the competency framework."""
    await _seed_framework(client, db)
    _, tok = await _counselor_with_school(client, db, seeded_school["school"])

    resp = await client.get("/api/v1/counselor/competencies", headers=_auth(tok))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    entry = data[0]
    assert "code" in entry
    assert "name_vi" in entry
    assert "source_ref" in entry


async def test_non_counselor_cannot_see_framework(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-100: a regular authenticated user without counselor membership is denied."""
    await _seed_framework(client, db)
    await _register(client, email="student_plain@weup-test.com", dob="2005-01-01")
    tok = await _token(client, "student_plain@weup-test.com")

    resp = await client.get("/api/v1/counselor/competencies", headers=_auth(tok))
    assert resp.status_code == 403, resp.text


async def test_unauthenticated_cannot_see_framework(client: AsyncClient, db: Database) -> None:
    """No token → 401."""
    resp = await client.get("/api/v1/counselor/competencies")
    assert resp.status_code == 401, resp.text


# -- POST /api/v1/me/counselor/self-assessments --------------------------------


async def test_counselor_creates_self_assessment(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-101/102: counselor can submit self-assessment and gets a development path."""
    await _seed_framework(client, db)
    _, tok = await _counselor_with_school(
        client, db, seeded_school["school"], email="c2@weup-test.com"
    )

    payload = {
        "scores": {"CC-01": 4, "CC-02": 2, "CC-03": 3, "CC-04": 1, "CC-05": 5, "CC-06": 2},
    }
    resp = await client.post(
        "/api/v1/me/counselor/self-assessments", json=payload, headers=_auth(tok)
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["version"] == 1
    assert "suggested_development_path" in data
    # Must carry a non-empty development path text (FR-102)
    assert len(data["suggested_development_path"]) > 0
    assert data["counselor_id"] is not None


async def test_self_assessment_version_increments(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-101: repeated submissions increment the version monotonically."""
    await _seed_framework(client, db)
    _, tok = await _counselor_with_school(
        client, db, seeded_school["school"], email="c3@weup-test.com"
    )

    payload = {"scores": {"CC-01": 3, "CC-02": 3}}
    r1 = await client.post(
        "/api/v1/me/counselor/self-assessments", json=payload, headers=_auth(tok)
    )
    assert r1.status_code == 201, r1.text
    assert r1.json()["version"] == 1

    r2 = await client.post(
        "/api/v1/me/counselor/self-assessments", json=payload, headers=_auth(tok)
    )
    assert r2.status_code == 201, r2.text
    assert r2.json()["version"] == 2


async def test_non_counselor_cannot_submit_self_assessment(
    client: AsyncClient, db: Database
) -> None:
    """Non-counselor user cannot POST self-assessments."""
    await _register(client, email="student_x@weup-test.com", dob="2005-01-01")
    tok = await _token(client, "student_x@weup-test.com")

    resp = await client.post(
        "/api/v1/me/counselor/self-assessments",
        json={"scores": {"CC-01": 3}},
        headers=_auth(tok),
    )
    assert resp.status_code == 403, resp.text


# -- GET /api/v1/me/counselor/self-assessments --------------------------------


async def test_counselor_lists_own_assessments(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-101: counselor can list their own assessment history."""
    await _seed_framework(client, db)
    _, tok = await _counselor_with_school(
        client, db, seeded_school["school"], email="c4@weup-test.com"
    )

    for score in [3, 4]:
        await client.post(
            "/api/v1/me/counselor/self-assessments",
            json={"scores": {"CC-01": score}},
            headers=_auth(tok),
        )

    resp = await client.get("/api/v1/me/counselor/self-assessments", headers=_auth(tok))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    # Latest first (version 2 before version 1)
    assert data[0]["version"] == 2
    assert data[1]["version"] == 1


async def test_counselor_only_sees_own_assessments(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """A counselor's list is scoped to themselves only."""
    await _seed_framework(client, db)
    _, tok1 = await _counselor_with_school(
        client, db, seeded_school["school"], email="c5a@weup-test.com"
    )
    _, tok2 = await _counselor_with_school(
        client, db, seeded_school["school"], email="c5b@weup-test.com"
    )

    # counselor A creates one assessment
    await client.post(
        "/api/v1/me/counselor/self-assessments",
        json={"scores": {"CC-01": 5}},
        headers=_auth(tok1),
    )

    # counselor B's list is empty
    resp = await client.get("/api/v1/me/counselor/self-assessments", headers=_auth(tok2))
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


# -- CP-1 separation: counselor without guardian can CRUD ---------------------


async def test_cp1_separation_counselor_no_guardian_needed(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-103 / CP-1 regression: counselor with NO guardian link or consent
    can create and read their own self-assessment.

    The guardian-consent gate is for under-16 student career data only. A
    counselor (adult) submitting their own professional self-assessment must
    NOT hit the consent gate.
    """
    await _seed_framework(client, db)
    # counselor registered with adult DOB, no guardian link set up at all
    user = await _register(client, email="counselor_nogdpr@weup-test.com", dob="1990-01-01")
    await enroll_membership(
        db, user_id=user["id"], school_id=seeded_school["school"], role="counselor"
    )
    tok = await _token(client, "counselor_nogdpr@weup-test.com")

    # POST — must succeed (no 403 from consent gate)
    post_resp = await client.post(
        "/api/v1/me/counselor/self-assessments",
        json={"scores": {"CC-01": 4, "CC-02": 3}},
        headers=_auth(tok),
    )
    assert post_resp.status_code == 201, (
        f"CP-1 separation violated: counselor blocked by consent gate — {post_resp.text}"
    )

    # GET — must succeed (no 403 from consent gate)
    get_resp = await client.get("/api/v1/me/counselor/self-assessments", headers=_auth(tok))
    assert get_resp.status_code == 200, (
        f"CP-1 separation violated: counselor list blocked by consent gate — {get_resp.text}"
    )
    assert len(get_resp.json()) == 1

    # Verify no student career data was touched (conceptual: no AssessmentResult
    # or Recommendation rows were created for this counselor's user_id).
    from app.assessments.models import AssessmentResult
    from app.reco.models import Recommendation
    from sqlalchemy import select

    async with db.session_factory() as s:
        ar = (
            await s.execute(select(AssessmentResult).where(AssessmentResult.user_id == user["id"]))
        ).first()
        rec = (
            await s.execute(select(Recommendation).where(Recommendation.user_id == user["id"]))
        ).first()
    assert ar is None, "Counselor self-assessment must NOT create student AssessmentResult rows"
    assert rec is None, "Counselor self-assessment must NOT create Recommendation rows"


# -- CP-4 unaffected: new endpoints do not widen authority -------------------


async def test_cp4_new_endpoints_do_not_widen_authority(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """CP-4 regression: new endpoints do not allow a counselor to read
    another counselor's self-assessments or a student's data.

    The only self-assessment list exposed is /me/counselor/self-assessments,
    which is always scoped to the calling user. No cross-user read endpoint
    is present in this module.
    """
    await _seed_framework(client, db)
    _counselor1_user, tok1 = await _counselor_with_school(
        client, db, seeded_school["school"], email="c6a@weup-test.com"
    )
    _counselor2_user, tok2 = await _counselor_with_school(
        client, db, seeded_school["school"], email="c6b@weup-test.com"
    )

    # counselor1 submits
    r = await client.post(
        "/api/v1/me/counselor/self-assessments",
        json={"scores": {"CC-01": 5}},
        headers=_auth(tok1),
    )
    assert r.status_code == 201, r.text

    # counselor2 sees only their own (empty) list — not counselor1's
    resp = await client.get("/api/v1/me/counselor/self-assessments", headers=_auth(tok2))
    assert resp.status_code == 200, resp.text
    assert resp.json() == [], "CP-4 violated: counselor2 must not see counselor1's self-assessments"

    # The school-reachability (has_counselor_access) is not touched by this module.
    # Verify the existing counselor-student reachability still works via the school
    # roster endpoint (independent of the new routes).
    roster_resp = await client.get(
        f"/api/v1/school/{seeded_school['school']}/students", headers=_auth(tok1)
    )
    # No students enrolled, but counselor has access (returns 200 + empty list)
    assert roster_resp.status_code == 200, roster_resp.text


# -- FR-102: development path has explanation --------------------------------


async def test_development_path_contains_explanation(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """FR-102: development path suggestion must carry a textual explanation."""
    await _seed_framework(client, db)
    _, tok = await _counselor_with_school(
        client, db, seeded_school["school"], email="c7@weup-test.com"
    )

    # Submit with low scores to force a suggestion
    low_scores = {f"CC-0{i}": 1 for i in range(1, 7)}
    resp = await client.post(
        "/api/v1/me/counselor/self-assessments",
        json={"scores": low_scores},
        headers=_auth(tok),
    )
    assert resp.status_code == 201, resp.text
    path = resp.json()["suggested_development_path"]
    # Path must be non-empty and explain something
    assert len(path) > 20, f"Development path too short to be meaningful: {path!r}"
