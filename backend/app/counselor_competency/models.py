"""Counselor-competency ORM models (spec.md §5, FR-100..103, ADR-016).

Two entities, fully independent of the learner 12-competency tree
(``app/competency/``):

- ``CounselorCompetency`` — the counseling-practice competency framework
  (ethics, listening, assessment-tool literacy, data safety/BVDLCN, referral
  recognition). Grounded in TT 18/2025. Read-only reference data; seeded.

- ``CounselorSelfAssessment`` — a versioned snapshot of a counselor's own
  self-rating against the framework. It is the counselor's personal development
  tool, NOT a KPI imposed by school_admin. Scores are stored as a
  semicolon-encoded ``CODE:rating`` string for SQLite/Postgres portability,
  matching the project convention in ``CareerProfile.riasec_codes``.

Privacy: self-assessment data belongs to the counselor (FR-103). It is NOT
within the guardian-consent scope (CP-1), which only covers under-16 student
career data. No student entity is referenced here.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UUIDMixin, utcnow


class CounselorCompetency(UUIDMixin, Base):
    """One counseling-practice competency in the professional framework (FR-100).

    ``code`` is a stable short identifier (e.g. ``CC-01``) used as the key in
    ``CounselorSelfAssessment.scores``. ``source_ref`` anchors each entry to the
    normative source (TT 18/2025 or a specific article thereof).
    """

    __tablename__ = "counselor_competency"
    __table_args__ = (Index("ix_counselor_competency_code", "code"),)

    code: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    name_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class CounselorSelfAssessment(UUIDMixin, Base):
    """A counselor's versioned self-assessment snapshot (FR-101, ADR-016).

    ``version`` is a monotonically increasing integer per counselor, so a
    counselor's full history is preserved. Each submission is a new row (no
    updates); the latest row has the highest ``version`` for a given
    ``counselor_id``.

    ``scores`` encodes per-competency self-ratings as ``CODE:rating`` pairs
    joined by ``';'``, e.g. ``CC-01:4;CC-02:2``. The schema layer converts
    to/from ``dict[str, int]``. This mirrors the comma/semicolon convention
    used in ``CareerProfile`` for SQLite portability (no ARRAY/JSON).

    ``suggested_development_path`` is free text produced at creation time by
    the service's suggestion logic (FR-102). It is NOT null; it always carries
    at least a brief explanation so the counselor understands the suggestion.

    Privacy: ``counselor_id`` is the owner. No query in this module crosses to
    another user's rows; no student data is referenced (CP-1 isolation).
    """

    __tablename__ = "counselor_self_assessment"
    __table_args__ = (
        Index("ix_counselor_self_assessment_counselor", "counselor_id"),
        # (counselor_id, version) together is unique — no duplicate versions per counselor.
        UniqueConstraint(
            "counselor_id", "version", name="uq_counselor_self_assessment_version"
        ),
    )

    counselor_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Semicolon-joined CODE:rating pairs (e.g. "CC-01:4;CC-02:2").
    scores: Mapped[str] = mapped_column(Text, nullable=False, default="")
    suggested_development_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
