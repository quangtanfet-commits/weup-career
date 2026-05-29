"""School-channel ORM models (spec.md §5, FR-80..83, CP-4).

The school channel is the B2B2C layer: schools, classes, the membership that
scopes a counselor/school_admin (and a student's enrollment) to one
``school_id``, and the Tier-3 counselling session record.

- ``School`` / ``SchoolClass`` — reference structure for a school and its classes.
- ``SchoolMembership`` — the single role-assignment + enrollment table. One row
  links a ``user_id`` to a ``school_id`` with a ``SchoolRole``
  (student | counselor | school_admin) and an optional ``class_id``. This is
  what makes ``counselor_check`` (CP-4) decidable: a counselor may reach a
  student iff both hold a membership in the SAME school (and, when the counselor
  row carries a ``class_id``, the same class/cohort). Membership — NOT the JWT —
  is the source of truth for the counselor/school_admin role, so authority is
  always re-derived from the DB and a counselor is never authorised outside
  their school.
- ``CounselingSession`` — a recorded Tier-1/2/3 counselling interaction between a
  counselor and a student (FR-81/82). ``notes`` is operational counselling
  prose, NOT sensitive-derived assessment data.

No raw sensitive assessment payload is ever stored or surfaced here; a
counselor's view of a student's profile is de-sensitized at the service layer
(FR-82/83, NFR-10).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import CounselingTier, SchoolRole
from app.core.models import UUIDMixin, utcnow


class School(UUIDMixin, Base):
    """A school in the B2B2C channel (FR-80)."""

    __tablename__ = "school"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    region: Mapped[str] = mapped_column(String(128), nullable=False, default="")


class SchoolClass(UUIDMixin, Base):
    """A class/cohort within a school (FR-80)."""

    __tablename__ = "school_class"
    __table_args__ = (Index("ix_school_class_school", "school_id"),)

    school_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    grade: Mapped[str] = mapped_column(String(16), nullable=False, default="")


class SchoolMembership(UUIDMixin, Base):
    """Links a user to a school with a role + optional class (FR-80/83, CP-4).

    A counselor/school_admin row scopes that staff member to ``school_id``; a
    student row is the student's enrollment (with optional ``class_id``). The
    ``counselor_check`` (CP-4) joins two membership rows on ``school_id`` (and,
    when the counselor row has a ``class_id``, on ``class_id``) to decide
    authority — default deny otherwise.
    """

    __tablename__ = "school_membership"
    __table_args__ = (
        # A user holds at most one membership per (school, role) — re-enrolling
        # or re-assigning is idempotent rather than duplicated.
        UniqueConstraint("user_id", "school_id", "role", name="uq_membership_user_school_role"),
        Index("ix_school_membership_user", "user_id"),
        Index("ix_school_membership_school_role", "school_id", "role"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    school_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("school.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[SchoolRole] = mapped_column(Enum(SchoolRole), nullable=False)
    # Optional class scoping. When a counselor row carries a class_id, the
    # counselor is authorised only for students in that class/cohort.
    class_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("school_class.id", ondelete="SET NULL"), nullable=True
    )


class CounselingSession(UUIDMixin, Base):
    """A recorded counselling session (FR-81/82, spec §5).

    ``notes`` is operational counselling prose only — never sensitive-derived
    assessment content. Creating a session is audited (FR-82).
    """

    __tablename__ = "counseling_session"
    __table_args__ = (
        Index("ix_counseling_session_counselor", "counselor_id"),
        Index("ix_counseling_session_student", "student_id"),
    )

    counselor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    tier: Mapped[CounselingTier] = mapped_column(Enum(CounselingTier), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
