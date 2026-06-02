"""School-channel API integration tests (slice 6, FR-80..83, CP-3/CP-4).

Exercises the real app + in-memory SQLite through the HTTP boundary. Counselor /
school_admin roles are DB-relational (``SchoolMembership``), so tests enrol users
via the ``enroll_membership`` helper (the school-admin flow stand-in) and assert
relational scoping: same-school access granted, cross-school hidden as 404.
"""

from __future__ import annotations

import pytest
from app.core.audit_models import AuditLog
from app.core.database import Database
from httpx import AsyncClient
from sqlalchemy import select

from tests.conftest import (
    child_dob,
    enroll_membership,
    mailer_of,
    register_and_verify,
)

pytestmark = pytest.mark.asyncio

_RIASEC_ANSWERS = {"I_1": 5, "I_2": 5, "R_1": 4, "A_1": 1, "S_1": 1, "E_1": 1, "C_1": 1}


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    # ``register_and_verify`` returns the login TokenResponse (``access_token`` +
    # ``user``); these school helpers only need the user record (``id``), so unwrap.
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


async def _counselor(client: AsyncClient, email: str = "counselor@example.com") -> str:
    """Register a staff user (a counselor is a normal account + a membership)."""
    user = await _register(client, email=email, dob="1985-01-01")
    return user["id"]


# -- GET /school/{id}/students (FR-80) ------------------------------------


async def test_counselor_sees_roster_of_own_school(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    counselor_id = await _counselor(client)
    student_id = await _student_with_consent(
        client, email="s1@example.com", parent_email="p1@example.com"
    )
    await enroll_membership(db, user_id=counselor_id, school_id=school, role="counselor")
    await enroll_membership(db, user_id=student_id, school_id=school, role="student")

    token = await _token(client, "counselor@example.com")
    resp = await client.get(f"/api/v1/school/{school}/students", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    emails = [r["email"] for r in resp.json()]
    assert "s1@example.com" in emails


async def test_school_admin_sees_roster(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    admin_id = await _counselor(client, email="admin@example.com")
    student_id = await _student_with_consent(
        client, email="s2@example.com", parent_email="p2@example.com"
    )
    await enroll_membership(db, user_id=admin_id, school_id=school, role="school_admin")
    await enroll_membership(db, user_id=student_id, school_id=school, role="student")

    token = await _token(client, "admin@example.com")
    resp = await client.get(f"/api/v1/school/{school}/students", headers=_auth(token))
    assert resp.status_code == 200, resp.text
    assert [r["email"] for r in resp.json()] == ["s2@example.com"]


async def test_counselor_other_school_roster_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """CP-4: a counselor with no membership in the school gets 404, not 403."""
    school = seeded_school["school"]
    outsider = await _counselor(client, email="outsider@example.com")
    # Enroll the outsider as a counselor of a DIFFERENT (ad-hoc) school id.
    await enroll_membership(
        db, user_id=outsider, school_id="00000000-0000-0000-0000-000000000999", role="counselor"
    )
    token = await _token(client, "outsider@example.com")
    resp = await client.get(f"/api/v1/school/{school}/students", headers=_auth(token))
    assert resp.status_code == 404


async def test_plain_student_cannot_list_roster_404(
    client: AsyncClient, seeded_school: dict[str, str]
) -> None:
    await _register(client, email="rando@example.com", dob="1990-01-01")
    token = await _token(client, "rando@example.com")
    resp = await client.get(
        f"/api/v1/school/{seeded_school['school']}/students", headers=_auth(token)
    )
    assert resp.status_code == 404


async def test_roster_requires_auth(client: AsyncClient, seeded_school: dict[str, str]) -> None:
    resp = await client.get(f"/api/v1/school/{seeded_school['school']}/students")
    assert resp.status_code == 401


# -- POST /counseling/sessions (FR-82, CP-4) ------------------------------


async def test_counselor_records_session_for_assigned_student(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    school = seeded_school["school"]
    counselor_id = await _counselor(client)
    student_id = await _student_with_consent(
        client, email="s3@example.com", parent_email="p3@example.com"
    )
    await enroll_membership(db, user_id=counselor_id, school_id=school, role="counselor")
    await enroll_membership(db, user_id=student_id, school_id=school, role="student")

    token = await _token(client, "counselor@example.com")
    resp = await client.post(
        "/api/v1/counseling/sessions",
        json={"student_id": student_id, "tier": "3", "notes": "Buổi tư vấn cá nhân"},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["student_id"] == student_id
    assert body["tier"] == "3"


async def test_counselor_session_unauthorized_student_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """CP-4: counselor cannot record a session for a student in another school."""
    school = seeded_school["school"]
    counselor_id = await _counselor(client)
    await enroll_membership(db, user_id=counselor_id, school_id=school, role="counselor")
    # Student enrolled in a DIFFERENT school.
    student_id = await _student_with_consent(
        client, email="s4@example.com", parent_email="p4@example.com"
    )
    await enroll_membership(
        db, user_id=student_id, school_id="00000000-0000-0000-0000-000000000888", role="student"
    )
    token = await _token(client, "counselor@example.com")
    resp = await client.post(
        "/api/v1/counseling/sessions",
        json={"student_id": student_id, "tier": "2", "notes": "x"},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_session_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/counseling/sessions", json={"student_id": "x", "tier": "1", "notes": ""}
    )
    assert resp.status_code == 401


# -- GET /school/students/{id}/progress (FR-82/83, CP-3, NFR-10) ----------


async def _enrolled_pair(
    client: AsyncClient, db: Database, school: str, *, same_school: bool = True
) -> tuple[str, str]:
    """Return (counselor_token-owner-id, student_id) with optional same-school."""
    counselor_id = await _counselor(client)
    student_id = await _student_with_consent(
        client, email="sp@example.com", parent_email="pp@example.com"
    )
    await enroll_membership(db, user_id=counselor_id, school_id=school, role="counselor")
    student_school = school if same_school else "00000000-0000-0000-0000-000000000777"
    await enroll_membership(db, user_id=student_id, school_id=student_school, role="student")
    return counselor_id, student_id


async def test_counselor_reads_desensitized_progress(
    client: AsyncClient,
    db: Database,
    seeded_school: dict[str, str],
    seeded_competencies: dict[str, str],
    seeded_instruments: dict[str, str],
) -> None:
    """FR-82/83 + CP-3: counselor sees de-sensitized progress; NO raw payload; audited."""
    school = seeded_school["school"]
    _, student_id = await _enrolled_pair(client, db, school)

    # Student takes a RIASEC assessment so there is a sensitive result to summarise.
    student_token = await _token(client, "sp@example.com")
    submit = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _RIASEC_ANSWERS},
        headers=_auth(student_token),
    )
    assert submit.status_code == 201, submit.text

    counselor_token = await _token(client, "counselor@example.com")
    resp = await client.get(
        f"/api/v1/school/students/{student_id}/progress", headers=_auth(counselor_token)
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["student_id"] == student_id
    assert len(body["progress"]) == 12  # the 12-competency tree, de-sensitized
    # De-sensitized assessment: instrument type + short derived code only — the
    # raw encrypted RIASEC payload / score vector / free text is NOT present.
    riasec = next(a for a in body["assessments"] if a["instrument_type"] == "riasec")
    assert riasec["summary_code"]  # a Holland code like "IRA"
    raw = resp.text
    assert "result_payload" not in raw
    assert "scores" not in raw  # the full score vector never crosses the boundary

    # CP-3: exactly one sensitive-access audit row naming counselor + student.
    async with db.session_factory() as s:
        rows = (
            (
                await s.execute(
                    select(AuditLog).where(
                        AuditLog.action == "counselor.student.progress.read",
                        AuditLog.is_sensitive_access.is_(True),
                        AuditLog.target_id == student_id,
                    )
                )
            )
            .scalars()
            .all()
        )
    assert len(rows) == 1
    assert rows[0].actor_id is not None and rows[0].actor_id != student_id


async def test_counselor_other_school_progress_404(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """CP-4: a counselor in a DIFFERENT school gets 404 on a student's progress."""
    school = seeded_school["school"]
    _, student_id = await _enrolled_pair(client, db, school, same_school=False)
    counselor_token = await _token(client, "counselor@example.com")
    resp = await client.get(
        f"/api/v1/school/students/{student_id}/progress", headers=_auth(counselor_token)
    )
    assert resp.status_code == 404


async def test_progress_no_audit_written_on_denied_read(
    client: AsyncClient, db: Database, seeded_school: dict[str, str]
) -> None:
    """A denied (cross-school) read must NOT write a sensitive-access audit row."""
    school = seeded_school["school"]
    _, student_id = await _enrolled_pair(client, db, school, same_school=False)
    counselor_token = await _token(client, "counselor@example.com")
    await client.get(
        f"/api/v1/school/students/{student_id}/progress", headers=_auth(counselor_token)
    )
    async with db.session_factory() as s:
        count = len(
            (
                await s.execute(
                    select(AuditLog).where(AuditLog.action == "counselor.student.progress.read")
                )
            )
            .scalars()
            .all()
        )
    assert count == 0


async def test_progress_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/school/students/x/progress")
    assert resp.status_code == 401
