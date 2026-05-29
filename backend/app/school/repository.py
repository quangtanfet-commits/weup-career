"""School-channel repository — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.

Every relational query here is the data-layer half of CP-4: a counselor's
authority over a student is decided by joining membership rows on ``school_id``
(and ``class_id`` when the counselor row is class-scoped), and roster reads are
filtered to the requested ``school_id``. There is no query that returns a
student outside the actor's school.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.auth.models import User
from app.core.enums import SchoolRole
from app.school.models import (
    CounselingSession,
    School,
    SchoolClass,
    SchoolMembership,
)


class ISchoolRepo(Protocol):
    async def add_school(self, school: School) -> School: ...
    async def add_class(self, klass: SchoolClass) -> SchoolClass: ...
    async def add_session(self, session: CounselingSession) -> CounselingSession: ...
    async def add_membership(self, membership: SchoolMembership) -> SchoolMembership: ...
    async def staff_membership(
        self, *, user_id: str, school_id: str
    ) -> SchoolMembership | None: ...
    async def admin_membership(
        self, *, user_id: str, school_id: str
    ) -> SchoolMembership | None: ...
    async def get_membership(
        self, *, user_id: str, school_id: str, role: SchoolRole
    ) -> SchoolMembership | None: ...
    async def has_counselor_access(self, *, counselor_id: str, student_id: str) -> bool: ...
    async def list_students(self, *, school_id: str) -> list[tuple[User, SchoolMembership]]: ...
    async def list_classes(self, *, school_id: str) -> list[SchoolClass]: ...
    async def find_counselor_for_student(self, *, student_id: str) -> str | None: ...


class SqlSchoolRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_school(self, school: School) -> School:
        self._session.add(school)
        await self._session.flush()
        return school

    async def add_class(self, klass: SchoolClass) -> SchoolClass:
        self._session.add(klass)
        await self._session.flush()
        return klass

    async def add_session(self, session: CounselingSession) -> CounselingSession:
        self._session.add(session)
        await self._session.flush()
        return session

    async def add_membership(self, membership: SchoolMembership) -> SchoolMembership:
        self._session.add(membership)
        await self._session.flush()
        return membership

    async def admin_membership(self, *, user_id: str, school_id: str) -> SchoolMembership | None:
        """A ``school_admin`` membership for this user in this school, else None.

        This is the authority gate for the school-admin write CRUD (FR-80): only
        a school_admin OF THIS school may create classes / [CRED_3D71BA7E] members.
        Re-derived from ``SchoolMembership`` per request — never from the JWT.
        """
        result = await self._session.execute(
            select(SchoolMembership).where(
                SchoolMembership.user_id == user_id,
                SchoolMembership.school_id == school_id,
                SchoolMembership.role == SchoolRole.SCHOOL_ADMIN,
            )
        )
        return result.scalars().first()

    async def get_membership(
        self, *, user_id: str, school_id: str, role: SchoolRole
    ) -> SchoolMembership | None:
        """An existing membership for the exact (user, school, role) tuple.

        Used to make enrollment idempotent against the
        ``uq_membership_user_school_role`` constraint.
        """
        result = await self._session.execute(
            select(SchoolMembership).where(
                SchoolMembership.user_id == user_id,
                SchoolMembership.school_id == school_id,
                SchoolMembership.role == role,
            )
        )
        return result.scalars().first()

    async def staff_membership(self, *, user_id: str, school_id: str) -> SchoolMembership | None:
        """A counselor OR school_admin membership for this user in this school.

        Used to authorise the roster read (``GET /school/{id}/students``): either
        staff role grants the scoped roster, nothing else does.
        """
        result = await self._session.execute(
            select(SchoolMembership).where(
                SchoolMembership.user_id == user_id,
                SchoolMembership.school_id == school_id,
                SchoolMembership.role.in_((SchoolRole.COUNSELOR, SchoolRole.SCHOOL_ADMIN)),
            )
        )
        return result.scalars().first()

    async def has_counselor_access(self, *, counselor_id: str, student_id: str) -> bool:
        """CP-4: True iff ``counselor_id`` is a counselor for ``student_id``.

        A counselor row and a student-enrollment row must exist in the SAME
        school. When the counselor row is class-scoped (``class_id`` not null),
        the student must be enrolled in that same class. A counselor in a
        different school (or for an unenrolled user) yields no row → False →
        404 at the edge (existence-hiding).
        """
        counselor = aliased(SchoolMembership)
        student = aliased(SchoolMembership)
        stmt = (
            select(counselor.id)
            .join(
                student,
                (counselor.school_id == student.school_id)
                & (
                    # Class scoping: if the counselor is bound to a class, the
                    # student's enrollment must be in that class. A counselor
                    # with no class_id is school-wide.
                    (counselor.class_id.is_(None)) | (counselor.class_id == student.class_id)
                ),
            )
            .where(
                counselor.user_id == counselor_id,
                counselor.role == SchoolRole.COUNSELOR,
                student.user_id == student_id,
                student.role == SchoolRole.STUDENT,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.first() is not None

    async def list_students(self, *, school_id: str) -> list[tuple[User, SchoolMembership]]:
        """The student roster of one school (FR-80), scoped to ``school_id``."""
        stmt = (
            select(User, SchoolMembership)
            .join(SchoolMembership, SchoolMembership.user_id == User.id)
            .where(
                SchoolMembership.school_id == school_id,
                SchoolMembership.role == SchoolRole.STUDENT,
            )
            .order_by(User.email)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def list_classes(self, *, school_id: str) -> list[SchoolClass]:
        """All classes of one school (FR-80), scoped to ``school_id``."""
        stmt = (
            select(SchoolClass).where(SchoolClass.school_id == school_id).order_by(SchoolClass.name)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_counselor_for_student(self, *, student_id: str) -> str | None:
        """A counselor user_id in the SAME school as ``student_id`` (FR-71).

        Joins the student's student-enrollment membership to a counselor
        membership on ``school_id`` (and on ``class_id`` when the counselor is
        class-scoped — same scoping rule as ``has_counselor_access``). Returns
        the first matching counselor's ``user_id``, or ``None`` if the student
        has no school or no counselor — the referral is then recorded unrouted.
        """
        student = aliased(SchoolMembership)
        counselor = aliased(SchoolMembership)
        stmt = (
            select(counselor.user_id)
            .join(
                student,
                (counselor.school_id == student.school_id)
                & ((counselor.class_id.is_(None)) | (counselor.class_id == student.class_id)),
            )
            .where(
                student.user_id == student_id,
                student.role == SchoolRole.STUDENT,
                counselor.role == SchoolRole.COUNSELOR,
            )
            .order_by(counselor.user_id)
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()
