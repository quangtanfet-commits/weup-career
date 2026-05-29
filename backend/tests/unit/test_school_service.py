"""Unit tests for school-channel internals (CP-4 class scoping, de-sensitization).

These exercise the repo + service directly against an in-memory session, where
HTTP-boundary tests would be heavier. Focus: the relational predicate
``has_counselor_access`` (incl. class scoping) and that the counselor view
yields ONLY de-sensitized signals.
"""

from __future__ import annotations

from datetime import date

import pytest
from app.auth.models import User
from app.core.enums import AccountStatus, AgeBand, SchoolRole, UserType
from app.core.models import new_uuid
from app.school.models import School, SchoolClass, SchoolMembership
from app.school.repository import SqlSchoolRepo
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def _user(session: AsyncSession, email: str) -> str:
    uid = new_uuid()
    session.add(
        User(
            id=uid,
            email=email,
            hashed_password="x",
            date_of_birth=date(2010, 1, 1),
            age_band=AgeBand.UNDER_16,
            user_type=UserType.STUDENT,
            account_status=AccountStatus.ACTIVE,
        )
    )
    await session.flush()
    return uid


async def _school(session: AsyncSession, name: str = "S") -> str:
    sid = new_uuid()
    session.add(School(id=sid, name=name, type="lower_secondary", region="HN"))
    await session.flush()
    return sid


async def _enroll(
    session: AsyncSession,
    *,
    user_id: str,
    school_id: str,
    role: SchoolRole,
    class_id: str | None = None,
) -> None:
    session.add(
        SchoolMembership(
            id=new_uuid(),
            user_id=user_id,
            school_id=school_id,
            role=role,
            class_id=class_id,
        )
    )
    await session.flush()


async def test_same_school_counselor_has_access(session: AsyncSession) -> None:
    repo = SqlSchoolRepo(session)
    school = await _school(session)
    c = await _user(session, "c@e.com")
    s = await _user(session, "s@e.com")
    await _enroll(session, user_id=c, school_id=school, role=SchoolRole.COUNSELOR)
    await _enroll(session, user_id=s, school_id=school, role=SchoolRole.STUDENT)
    assert await repo.has_counselor_access(counselor_id=c, student_id=s) is True


async def test_different_school_counselor_denied(session: AsyncSession) -> None:
    repo = SqlSchoolRepo(session)
    sch_a = await _school(session, "A")
    sch_b = await _school(session, "B")
    c = await _user(session, "c@e.com")
    s = await _user(session, "s@e.com")
    await _enroll(session, user_id=c, school_id=sch_a, role=SchoolRole.COUNSELOR)
    await _enroll(session, user_id=s, school_id=sch_b, role=SchoolRole.STUDENT)
    assert await repo.has_counselor_access(counselor_id=c, student_id=s) is False


async def test_class_scoped_counselor_only_sees_own_class(session: AsyncSession) -> None:
    """A class-scoped counselor reaches a same-class student but not another class."""
    repo = SqlSchoolRepo(session)
    school = await _school(session)
    class_a = new_uuid()
    class_b = new_uuid()
    session.add(SchoolClass(id=class_a, school_id=school, name="9A", grade="9"))
    session.add(SchoolClass(id=class_b, school_id=school, name="9B", grade="9"))
    await session.flush()

    c = await _user(session, "c@e.com")
    s_a = await _user(session, "sa@e.com")
    s_b = await _user(session, "sb@e.com")
    await _enroll(session, user_id=c, school_id=school, role=SchoolRole.COUNSELOR, class_id=class_a)
    await _enroll(session, user_id=s_a, school_id=school, role=SchoolRole.STUDENT, class_id=class_a)
    await _enroll(session, user_id=s_b, school_id=school, role=SchoolRole.STUDENT, class_id=class_b)

    assert await repo.has_counselor_access(counselor_id=c, student_id=s_a) is True
    assert await repo.has_counselor_access(counselor_id=c, student_id=s_b) is False


async def test_school_wide_counselor_sees_any_class(session: AsyncSession) -> None:
    """A counselor with no class_id is school-wide (reaches a classed student)."""
    repo = SqlSchoolRepo(session)
    school = await _school(session)
    class_a = new_uuid()
    session.add(SchoolClass(id=class_a, school_id=school, name="9A", grade="9"))
    await session.flush()
    c = await _user(session, "c@e.com")
    s = await _user(session, "s@e.com")
    await _enroll(session, user_id=c, school_id=school, role=SchoolRole.COUNSELOR)  # no class
    await _enroll(session, user_id=s, school_id=school, role=SchoolRole.STUDENT, class_id=class_a)
    assert await repo.has_counselor_access(counselor_id=c, student_id=s) is True


async def test_school_admin_is_not_a_counselor_for_access(session: AsyncSession) -> None:
    """A school_admin membership does NOT grant counselor↔student data access (CP-4)."""
    repo = SqlSchoolRepo(session)
    school = await _school(session)
    a = await _user(session, "a@e.com")
    s = await _user(session, "s@e.com")
    await _enroll(session, user_id=a, school_id=school, role=SchoolRole.SCHOOL_ADMIN)
    await _enroll(session, user_id=s, school_id=school, role=SchoolRole.STUDENT)
    assert await repo.has_counselor_access(counselor_id=a, student_id=s) is False


async def test_list_students_scoped_to_school(session: AsyncSession) -> None:
    repo = SqlSchoolRepo(session)
    school = await _school(session)
    other = await _school(session, "Other")
    s1 = await _user(session, "in@e.com")
    s2 = await _user(session, "out@e.com")
    await _enroll(session, user_id=s1, school_id=school, role=SchoolRole.STUDENT)
    await _enroll(session, user_id=s2, school_id=other, role=SchoolRole.STUDENT)
    rows = await repo.list_students(school_id=school)
    assert [u.email for u, _ in rows] == ["in@e.com"]


async def test_staff_membership_matches_counselor_and_admin(session: AsyncSession) -> None:
    repo = SqlSchoolRepo(session)
    school = await _school(session)
    c = await _user(session, "c@e.com")
    a = await _user(session, "a@e.com")
    none_user = await _user(session, "n@e.com")
    await _enroll(session, user_id=c, school_id=school, role=SchoolRole.COUNSELOR)
    await _enroll(session, user_id=a, school_id=school, role=SchoolRole.SCHOOL_ADMIN)
    assert await repo.staff_membership(user_id=c, school_id=school) is not None
    assert await repo.staff_membership(user_id=a, school_id=school) is not None
    assert await repo.staff_membership(user_id=none_user, school_id=school) is None


async def test_desensitized_view_vips_exposes_presence_only(
    session: AsyncSession,
    seeded_competencies: dict[str, str],
    seeded_instruments: dict[str, str],
) -> None:
    """A VIPS result surfaces as presence only — no derived code, no free text."""
    import json

    from app.assessments.models import AssessmentResult
    from app.auth.repository import SqlUserRepo
    from app.competency.repository import SqlCompetencyRepo
    from app.competency.service import CompetencyService
    from app.core.audit import SqlAuditRepo
    from app.core.crypto import FieldCrypto
    from app.core.enums import InstrumentType
    from app.guardians.repository import SqlGuardianRepo
    from app.reco.repository import SqlRecoRepo
    from app.school.service import SchoolService

    crypto = FieldCrypto("test-field-key")
    student = await _user(session, "stu@e.com")
    # Persist a VIPS result whose payload has NO "code" field (presence only).
    vips_instrument_id = seeded_instruments[InstrumentType.VIPS.value]
    session.add(
        AssessmentResult(
            id=new_uuid(),
            user_id=student,
            instrument_id=vips_instrument_id,
            result_payload=crypto.encrypt(json.dumps({"dominant": "values"})),
            key_version=crypto.key_version,
            is_sensitive=True,
            version=1,
        )
    )
    await session.flush()

    audit = SqlAuditRepo(session)
    comp = CompetencyService(
        competencies=SqlCompetencyRepo(session),
        users=SqlUserRepo(session),
        audit=audit,
    )
    svc = SchoolService(
        school=SqlSchoolRepo(session),
        guardians=SqlGuardianRepo(session),
        competency=comp,
        reco=SqlRecoRepo(session),
        audit=audit,
        crypto=crypto,
    )
    # Owner reads own data (can_access True via actor==owner) → VIPS code None,
    # so the VIPS branch returns presence-only without decrypting a "code".
    view = await svc.read_student_progress(counselor_id=student, student_id=student)
    vips = next(a for a in view.assessments if a.instrument_type == "vips")
    assert vips.summary_code is None
