"""Wellbeing ORM model: SupportRequest (FR-71).

A ``SupportRequest`` is a **referral/routing record** — a student asks for
support and the system routes the request to a counselor in the student's
school (Tier 3). It deliberately carries NO diagnosis, NO risk score, and NO
clinical assessment (NG-03): only the requesting student, the routed counselor
(nullable — none assigned if the student has no school counselor yet), a free
``message`` (the student's own words), a coarse ``status``, and timestamps.
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
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import CounselingTier, SupportRequestStatus
from app.core.models import UUIDMixin, utcnow


class SupportRequest(UUIDMixin, Base):
    """A student's request for counselor support, routed as a Tier-3 referral.

    NO medical/clinical fields by construction (NG-03). ``tier`` is fixed at
    Tier 3 (individual counselling pathway). ``counselor_id`` is the routed
    counselor in the student's school, or NULL when none is available — the
    request is still recorded gracefully so it is never silently dropped.
    """

    __tablename__ = "support_request"
    __table_args__ = (
        Index("ix_support_request_student", "student_id"),
        Index("ix_support_request_counselor", "counselor_id"),
    )

    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    # The counselor the referral was routed to (same school). Nullable: if the
    # student has no school counselor, the request is recorded unrouted rather
    # than rejected.
    counselor_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    tier: Mapped[CounselingTier] = mapped_column(Enum(CounselingTier), nullable=False)
    # The student's own words. Not clinical content; free text the student chose
    # to share when asking for support.
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[SupportRequestStatus] = mapped_column(
        Enum(SupportRequestStatus), nullable=False, default=SupportRequestStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
