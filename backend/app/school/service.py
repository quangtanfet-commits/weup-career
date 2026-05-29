"""SchoolService — roster, counselling sessions, counselor-scoped reads (CP-4/CP-3).

Pure business logic, no FastAPI imports (hexagonal, ADR-009).

Three responsibilities, all default-deny:

- **Roster (FR-80).** ``list_students`` returns a school's student roster only
  if the actor holds a counselor/school_admin membership in THAT school; cross-
  school → ``NotFoundError`` (404, existence-hiding per auth-design.md).
- **Counselling sessions (FR-81/82).** ``create_session`` records a session only
  when the counselor is authorised for that student via the relational
  ``can_access`` (CP-4); otherwise 404. Always audited.
- **De-sensitized student view (FR-82/83, NFR-10).** ``read_student_progress``
  lets an authorised counselor see a student's competency progress + a
  de-sensitized assessment SUMMARY (Holland/RIASEC code + which instruments are
  taken) — never the raw encrypted RIASEC/VIPS/MBTI payload. EVERY such read
  writes a CP-3 audit row (``is_sensitive_access=True``) naming counselor +
  student, in the same transaction (fail-closed).

The counselor↔student decision is delegated to ``app.core.authz.can_access``
with this service's ``counselor_check`` hook, so the guardian path is reused
unchanged and there is one place that decides relational access.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.auth.repository import IUserRepo
from app.competency.service import CompetencyProgress, CompetencyService
from app.core.audit import IAuditRepo
from app.core.authz import can_access
from app.core.crypto import FieldCrypto
from app.core.enums import CounselingTier, InstrumentType, SchoolRole
from app.core.exceptions import NotFoundError
from app.core.models import new_uuid
from app.core.trace import emit as trace_emit
from app.guardians.repository import IGuardianRepo
from app.reco.repository import IRecoRepo
from app.school.models import CounselingSession, SchoolClass, SchoolMembership
from app.school.repository import ISchoolRepo


@dataclass(frozen=True)
class RosterEntry:
    """A student roster row (de-sensitized: identity + enrollment only)."""

    user_id: str
    email: str
    class_id: str | None


@dataclass(frozen=True)
class DesensitizedAssessment:
    """A de-sensitized assessment summary for a counselor (FR-82/83, NFR-10).

    Carries ONLY non-free-text signals: the instrument type and a short
    derived code (e.g. RIASEC Holland code / MBTI code). The raw encrypted
    payload and any free-text content never leave the sensitive boundary.
    """

    instrument_type: str
    summary_code: str | None


@dataclass(frozen=True)
class StudentProgressView:
    """A counselor's de-sensitized view of an assigned student (FR-82)."""

    student_id: str
    progress: list[CompetencyProgress]
    assessments: list[DesensitizedAssessment]


class SchoolService:
    def __init__(
        self,
        *,
        school: ISchoolRepo,
        guardians: IGuardianRepo,
        competency: CompetencyService,
        reco: IRecoRepo,
        audit: IAuditRepo,
        crypto: FieldCrypto,
        users: IUserRepo,
    ) -> None:
        self._school = school
        self._guardians = guardians
        self._competency = competency
        self._reco = reco
        self._audit = audit
        self._crypto = crypto
        self._users = users

    # -- CP-4 relational hook ---------------------------------------------

    async def counselor_check(self, actor_id: str, owner_id: str) -> bool:
        """Is ``actor_id`` a counselor for ``owner_id``? (CP-4, default deny).

        Shaped (positional, async-bool) to slot straight into
        ``can_access(counselor_check=...)`` so the guardian↔child path is reused
        untouched and counselor↔student is the only thing this slice adds.
        """
        return await self._school.has_counselor_access(counselor_id=actor_id, student_id=owner_id)

    async def _can_access(self, *, actor_id: str, owner_id: str) -> bool:
        return await can_access(
            actor_id=actor_id,
            owner_id=owner_id,
            guardian_repo=self._guardians,
            counselor_check=self.counselor_check,
        )

    # -- roster (FR-80) ----------------------------------------------------

    async def list_students(self, *, actor_id: str, school_id: str) -> list[RosterEntry]:
        """Roster of a school for an authorised staff member (FR-80).

        Authorised = counselor OR school_admin membership in that school.
        Anyone else (incl. a counselor of a different school) gets 404.
        """
        staff = await self._school.staff_membership(user_id=actor_id, school_id=school_id)
        if staff is None:
            raise NotFoundError("Không tìm thấy trường")

        rows = await self._school.list_students(school_id=school_id)
        return [
            RosterEntry(user_id=user.id, email=user.email, class_id=membership.class_id)
            for user, membership in rows
        ]

    # -- school_admin write CRUD (FR-80, G-7, CP-4 spirit) -----------------

    async def _require_admin(self, *, actor_id: str, school_id: str) -> None:
        """Authorise a school_admin OF this school, else 404 (existence-hiding).

        Authority is re-derived from ``SchoolMembership`` (never the JWT). A
        non-admin, or an admin of a DIFFERENT school, is told the school does
        not exist (404) rather than 403, per auth-design.md — a school_admin can
        never manage a school they do not administer.
        """
        admin = await self._school.admin_membership(user_id=actor_id, school_id=school_id)
        if admin is None:
            raise NotFoundError("Không tìm thấy trường")

    async def create_class(
        self, *, actor_id: str, school_id: str, name: str, grade: str
    ) -> SchoolClass:
        """Create a class in ``school_id`` (FR-80). Admin-of-this-school only."""
        await self._require_admin(actor_id=actor_id, school_id=school_id)
        klass = await self._school.add_class(
            SchoolClass(id=new_uuid(), school_id=school_id, name=name, grade=grade)
        )
        await self._audit.record(
            action="school.class.created",
            actor_id=actor_id,
            target_type="SchoolClass",
            target_id=klass.id,
        )
        return klass

    async def list_classes(self, *, actor_id: str, school_id: str) -> list[SchoolClass]:
        """List classes of ``school_id`` (FR-80).

        Authorised for a school_admin OR counselor of that school (same gate as
        the roster read); anyone else → 404.
        """
        staff = await self._school.staff_membership(user_id=actor_id, school_id=school_id)
        if staff is None:
            raise NotFoundError("Không tìm thấy trường")
        return await self._school.list_classes(school_id=school_id)

    async def assign_member(
        self,
        *,
        actor_id: str,
        school_id: str,
        user_id: str,
        role: SchoolRole,
        class_id: str | None = None,
    ) -> tuple[SchoolMembership, bool]:
        """Enroll/assign ``user_id`` as student or counselor in ``school_id``.

        Admin-of-this-school only (FR-80). Returns ``(membership, created)``;
        idempotent on the ``(user, school, role)`` unique constraint — assigning
        an already-assigned (user, role) returns the existing row with
        ``created=False`` instead of crashing on the duplicate. The target user
        must exist (else 404). Only ``student``/``counselor`` may be assigned via
        this flow (assigning another admin is out of scope).
        """
        await self._require_admin(actor_id=actor_id, school_id=school_id)

        if role not in (SchoolRole.STUDENT, SchoolRole.COUNSELOR):
            raise NotFoundError("Vai trò không hợp lệ cho luồng phân công")

        target = await self._users.get_by_id(user_id)
        if target is None:
            raise NotFoundError("Không tìm thấy người dùng")

        existing = await self._school.get_membership(
            user_id=user_id, school_id=school_id, role=role
        )
        if existing is not None:
            return existing, False

        membership = await self._school.add_membership(
            SchoolMembership(
                id=new_uuid(),
                user_id=user_id,
                school_id=school_id,
                role=role,
                class_id=class_id,
            )
        )
        await self._audit.record(
            action="school.member.assigned",
            actor_id=actor_id,
            target_type="SchoolMembership",
            target_id=membership.id,
        )
        return membership, True

    # -- counselling sessions (FR-81/82) -----------------------------------

    async def create_session(
        self, *, counselor_id: str, student_id: str, tier: CounselingTier, notes: str
    ) -> CounselingSession:
        """Record a counselling session for an authorised student (FR-82, CP-4).

        The counselor may only create a session for a student they are
        authorised for; an unauthorised (e.g. different-school) student is not
        found → 404. The session row is audited.
        """
        if not await self._school.has_counselor_access(
            counselor_id=counselor_id, student_id=student_id
        ):
            raise NotFoundError("Không tìm thấy học sinh")

        session = CounselingSession(
            id=new_uuid(),
            counselor_id=counselor_id,
            student_id=student_id,
            tier=tier,
            notes=notes,
        )
        await self._school.add_session(session)
        await self._audit.record(
            action="counseling.session.created",
            actor_id=counselor_id,
            target_type="CounselingSession",
            target_id=session.id,
        )
        return session

    # -- de-sensitized student view (FR-82/83, NFR-10, CP-3) ---------------

    async def read_student_progress(
        self, *, counselor_id: str, student_id: str
    ) -> StudentProgressView:
        """A counselor's de-sensitized view of an assigned student (FR-82).

        Returns competency progress (depth/dev_phase — already de-sensitized) and
        a de-sensitized assessment summary (instrument type + derived code only;
        NO raw encrypted payload, NO free text — FR-83/NFR-10). Authority is the
        relational ``can_access`` (owner / verified guardian / assigned
        counselor); cross-relation → 404.

        CP-3: because the student's sensitive-derived data is being read by
        another human, exactly one ``is_sensitive_access=True`` audit row is
        written (counselor + student) in the same transaction, BEFORE returning.
        If the audit write fails, the read fails closed.
        """
        if not await self._can_access(actor_id=counselor_id, owner_id=student_id):
            raise NotFoundError("Không tìm thấy học sinh")

        # CP-3: one sensitive-access audit per counselor read, same transaction,
        # written before any payload is assembled.
        await self._audit.record(
            action="counselor.student.progress.read",
            actor_id=counselor_id,
            target_type="User",
            target_id=student_id,
            is_sensitive_access=True,
        )

        progress = await self._competency.get_progress(user_id=student_id)
        assessments = await self._desensitized_assessments(student_id=student_id)

        trace_emit(
            "CounselorReadStudent",
            user=counselor_id,
            state={"student": student_id, "sensitiveAccess": True},
        )
        return StudentProgressView(
            student_id=student_id, progress=progress, assessments=assessments
        )

    async def _desensitized_assessments(self, *, student_id: str) -> list[DesensitizedAssessment]:
        """Strip each latest result down to a non-free-text summary code.

        Decrypts only to extract the derived ``code`` (Holland/MBTI) — a short
        category label, not free text and not the full score vector. The raw
        ciphertext and any narrative content never cross into the counselor view
        (FR-83, NFR-10).
        """
        results = await self._reco.latest_results(student_id)
        out: list[DesensitizedAssessment] = []
        for result, instrument in results:
            summary_code: str | None = None
            if instrument.type in (InstrumentType.RIASEC, InstrumentType.MBTI):
                payload = json.loads(self._crypto.decrypt(result.result_payload))
                code = payload.get("code") if isinstance(payload, dict) else None
                summary_code = str(code) if code else None
            # VIPS and anything else: expose presence only, no derived content.
            out.append(
                DesensitizedAssessment(
                    instrument_type=instrument.type.value, summary_code=summary_code
                )
            )
        return out
