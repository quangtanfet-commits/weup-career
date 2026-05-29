"""Competency domain ORM models (spec.md §5, FR-20..24, ADR-013).

Two orthogonal axes (ADR-013):

- **Depth axis (measurement):** ``Indicator.depth ∈ {K, A, R}`` (NCDG / [CRED_C7E1A8FB]
  2018). ``LearnerProgress`` records ``(user, competency, depth_achieved)`` and
  is **append-only** — depth only advances K→A→R, history is never overwritten
  (CP-8, spec §8).
- **Development-phase axis (positioning):** ``LearnerDomainPhase.dev_phase ∈
  {awareness, exploration, planning}`` (ECG). One row per (user, area); a
  ``working`` user may legitimately hold several phases at once across areas
  (non-linear ABCD), so this table allows multiple rows per user.

The competency tree itself (12 ``Competency`` with their ``Indicator`` set) is
fixed reference data, seeded idempotently (see ``competency/seed.py``).
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
from app.core.enums import CompetencyArea, Depth, DevPhase
from app.core.models import UUIDMixin, utcnow


class Competency(UUIDMixin, Base):
    """One of the 12 fixed ABCD competencies (code NL1..NL12).

    ``dieu5_codes`` is the legal crosswalk to TT 16/2026 Điều 5 (stored as a
    comma-joined string for portability across SQLite/Postgres; exposed as a
    list by the schema layer).
    """

    __tablename__ = "competency"
    __table_args__ = (Index("ix_competency_area", "area"),)

    code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    area: Mapped[CompetencyArea] = mapped_column(Enum(CompetencyArea), nullable=False)
    name_vi: Mapped[str] = mapped_column(String(255), nullable=False)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # Comma-joined Điều 5 codes (e.g. "a,b"). Schema layer splits to a list.
    dieu5_codes: Mapped[str] = mapped_column(String(64), nullable=False, default="")


class Indicator(UUIDMixin, Base):
    """A NCDG-style behavioural indicator at one depth (K/A/R) of a competency."""

    __tablename__ = "indicator"
    __table_args__ = (Index("ix_indicator_competency_depth", "competency_id", "depth"),)

    competency_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False
    )
    depth: Mapped[Depth] = mapped_column(Enum(Depth), nullable=False)
    statement_vi: Mapped[str] = mapped_column(Text, nullable=False)
    dieu5_code: Mapped[str] = mapped_column(String(8), nullable=False, default="b")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False, default="")


class LearnerProgress(UUIDMixin, Base):
    """Append-only record that a learner reached ``depth_achieved`` on a competency.

    CP-8: rows are only ever inserted (never updated/deleted by the service);
    each represents a depth attainment event. The *current* depth for a
    (user, competency) is the max ``depth_achieved`` across that learner's rows.
    """

    __tablename__ = "learner_progress"
    __table_args__ = (Index("ix_learner_progress_user_competency", "user_id", "competency_id"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    competency_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competency.id", ondelete="CASCADE"), nullable=False
    )
    depth_achieved: Mapped[Depth] = mapped_column(Enum(Depth), nullable=False)
    evidence_ref: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class LearnerDomainPhase(UUIDMixin, Base):
    """A learner's development phase for one ABCD area (ECG axis, FR-23).

    Students: inferred from ``school_level`` with allowed personal deviation.
    Working users: multiple rows (one phase per area) model the non-linear
    ABCD layer. Latest ``set_at`` per (user, area) is the phase in force.
    """

    __tablename__ = "learner_domain_phase"
    __table_args__ = (Index("ix_learner_domain_phase_user_area", "user_id", "area"),)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    area: Mapped[CompetencyArea] = mapped_column(Enum(CompetencyArea), nullable=False)
    dev_phase: Mapped[DevPhase] = mapped_column(Enum(DevPhase), nullable=False)
    set_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
