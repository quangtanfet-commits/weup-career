"""school_admin write-CRUD API tests (slice 7, FR-80, G-7, CP-4 spirit).

A school_admin manages classes/members ONLY within their own ``school_id``;
authority is re-derived from ``SchoolMembership`` (never the JWT). Cross-school
or non-admin actors are hidden as 404 (existence-hiding, auth-design.md);
plain non-staff get 404 too. Writes are audited; member assignment is
idempotent on the ``(user, school, role)`` unique constraint.
"""

from __future__ import annotations

import pytest
from app.core.audit_models import AuditLog
from app.core.database import Database
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import enroll_membership, register_payload

pytestmark = pytest.mark.asyncio

_OTHER_SCHOOL = "00000000-0000-0000-0000-0000000000aa"


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/register", json=register_payload(**kw))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _admin_of(client: AsyncClient, db: Database, school: str, email: str) -> str:
    user = await _register(client, email=email, dob="1980-01-01")
    await enroll_membership(db, user_id=user["id"], school_id=school, role="school_admin")
    return user["id"]


# -- POST /school/{id}/classes --------------------------------------------


async def test_admin_creates_class_in_own_school(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin1@example.com")
    token = await _token(client, "admin1@example.com")

    resp = await client.post(
        f"/api/v1/school/{school}/classes",
        json={"name": "10A1", "grade": "10"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["name"] == "10A1"
    assert body["school_id"] == school

    # Audited.
    async with db.session_factory() as s:
        rows = (
            (await s.execute(select(AuditLog).where(AuditLog.action == "school.class.created")))
            .scalars()
            .all()
        )
    assert len(rows) == 1


async def test_admin_cannot_create_class_in_other_school_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """A school_admin acting on a DIFFERENT school is hidden as 404."""
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin2@example.com")
    token = await _token(client, "admin2@example.com")
    resp = await client.post(
        f"/api/v1/school/{_OTHER_SCHOOL}/classes",
        json={"name": "X", "grade": "10"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_student_cannot_create_class_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """A non-admin (plain student account) cannot create a class → 404."""
    school = seeded_school["school"]
    user = await _register(client, email="plain@example.com", dob="1990-01-01")
    await enroll_membership(db, user_id=user["id"], school_id=school, role="student")
    token = await _token(client, "plain@example.com")
    resp = await client.post(
        f"/api/v1/school/{school}/classes",
        json={"name": "X", "grade": "9"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_counselor_cannot_create_class_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """A counselor (staff, but not admin) cannot create a class → 404."""
    school = seeded_school["school"]
    user = await _register(client, email="couns@example.com", dob="1985-01-01")
    await enroll_membership(db, user_id=user["id"], school_id=school, role="counselor")
    token = await _token(client, "couns@example.com")
    resp = await client.post(
        f"/api/v1/school/{school}/classes",
        json={"name": "X", "grade": "9"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_create_class_requires_auth(
    client: AsyncClient, seeded_school: dict[str, str]
) -> None:
    resp = await client.post(
        f"/api/v1/school/{seeded_school['school']}/classes", json={"name": "X", "grade": "9"}
    )
    assert resp.status_code == 401


# -- GET /school/{id}/classes ---------------------------------------------


async def test_admin_lists_classes(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin3@example.com")
    token = await _token(client, "admin3@example.com")
    await client.post(
        f"/api/v1/school/{school}/classes",
        json={"name": "11B", "grade": "11"},
        headers=_auth(token),
    )
    resp = await client.get(f"/api/v1/school/{school}/classes", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    names = [c["name"] for c in resp.json()]
    # The seeded demo class "9A" + the freshly created "11B".
    assert "11B" in names and "9A" in names


async def test_counselor_lists_classes(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """A counselor of the school may also list classes (same gate as roster)."""
    school = seeded_school["school"]
    user = await _register(client, email="couns2@example.com", dob="1985-01-01")
    await enroll_membership(db, user_id=user["id"], school_id=school, role="counselor")
    token = await _token(client, "couns2@example.com")
    resp = await client.get(f"/api/v1/school/{school}/classes", headers=_auth(token))
    assert resp.status_code == 200, resp.text


async def test_outsider_lists_classes_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _register(client, email="rando2@example.com", dob="1990-01-01")
    token = await _token(client, "rando2@example.com")
    resp = await client.get(f"/api/v1/school/{school}/classes", headers=_auth(token))
    assert resp.status_code == 404


async def test_list_classes_requires_auth(
    client: AsyncClient, seeded_school: dict[str, str]
) -> None:
    resp = await client.get(f"/api/v1/school/{seeded_school['school']}/classes")
    assert resp.status_code == 401


# -- POST /school/{id}/members --------------------------------------------


async def test_admin_assigns_student_member(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin4@example.com")
    target = await _register(
        client, email="newstu@example.com", dob="2012-01-01", school_level="lower_secondary"
    )
    token = await _token(client, "admin4@example.com")

    resp = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": target["id"], "role": "student"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["created"] is True
    assert body["role"] == "student"
    assert body["user_id"] == target["id"]

    # The new student now appears on the roster.
    roster = await client.get(f"/api/v1/school/{school}/students", headers=_auth(token))
    assert "newstu@example.com" in [r["email"] for r in roster.json()]


async def test_admin_assigns_counselor_member(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin5@example.com")
    target = await _register(client, email="newcouns@example.com", dob="1988-01-01")
    token = await _token(client, "admin5@example.com")
    resp = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": target["id"], "role": "counselor"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["role"] == "counselor"


async def test_assign_member_idempotent(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """Re-assigning the same (user, role) returns the existing row, no crash."""
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin6@example.com")
    target = await _register(
        client, email="dup@example.com", dob="2012-01-01", school_level="lower_secondary"
    )
    token = await _token(client, "admin6@example.com")
    first = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": target["id"], "role": "student"},
        headers=_auth(token),
    )
    assert first.status_code == 201
    assert first.json()["created"] is True

    second = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": target["id"], "role": "student"},
        headers=_auth(token),
    )
    assert second.status_code == 201, second.text
    assert second.json()["created"] is False
    assert second.json()["id"] == first.json()["id"]


async def test_admin_assign_in_other_school_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin7@example.com")
    target = await _register(
        client, email="t7@example.com", dob="2012-01-01", school_level="lower_secondary"
    )
    token = await _token(client, "admin7@example.com")
    resp = await client.post(
        f"/api/v1/school/{_OTHER_SCHOOL}/members",
        json={"user_id": target["id"], "role": "student"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_student_cannot_assign_member_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    actor = await _register(client, email="notadmin@example.com", dob="1990-01-01")
    await enroll_membership(db, user_id=actor["id"], school_id=school, role="student")
    target = await _register(client, email="t8@example.com", dob="1991-01-01")
    token = await _token(client, "notadmin@example.com")
    resp = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": target["id"], "role": "student"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_assign_unknown_user_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin9@example.com")
    token = await _token(client, "admin9@example.com")
    resp = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": "no-such-user", "role": "student"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_assign_admin_role_rejected_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """Assigning another school_admin is out of scope for this flow → 404."""
    school = seeded_school["school"]
    await _admin_of(client, db, school, "admin10@example.com")
    target = await _register(client, email="t10@example.com", dob="1980-01-01")
    token = await _token(client, "admin10@example.com")
    resp = await client.post(
        f"/api/v1/school/{school}/members",
        json={"user_id": target["id"], "role": "school_admin"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_assign_member_requires_auth(
    client: AsyncClient, seeded_school: dict[str, str]
) -> None:
    resp = await client.post(
        f"/api/v1/school/{seeded_school['school']}/members",
        json={"user_id": "x", "role": "student"},
    )
    assert resp.status_code == 401
