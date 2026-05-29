"""Careers domain ORM models (spec.md §5, FR-30..33/40..42/50..51, ADR-013).

This module backs the **public career library** (TT 16/2026 Điều 5(a)) plus the
versioned learning content for career-selection skills (Điều 5(c)) and career
experience (Điều 5(d)).

- ``CareerProfile`` — one occupation/nghề: RIASEC interest tags, required
  competencies, training paths prose, labour-market outlook, transparent
  ``source_ref`` and content ``version`` (FR-33 — change = new version). Linked
  to one or more ``Pathway`` rows via ``career_pathway`` so the **GDNN /
  "trường trung học nghề"** route (Luật GDNN 124/2025) is reachable and
  filterable, not just academic university study (FR-31).
- ``Pathway`` — a phân luồng route (academic | vocational_secondary | gdnn |
  labor), reference data.
- ``ContentItem`` — a versioned unit of learning content for Điều 5(c)/(d),
  tagged with ``dieu5_code`` + ``competency_code`` + ``depth`` + ``dev_phase`` +
  ``school_level`` + publication ``status`` (FR-90, NFR-26).

All of this is **public content** (Điều 5(a)): an under-16 awaiting guardian
consent may still read it (ADR-001 note, guardian-verification.md), so the
router applies Bearer auth only — never the career-data consent gate.
"""

from __future__ import annotations

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import (
    ContentStatus,
    Depth,
    DevPhase,
    PathwayType,
    SchoolLevel,
    TrainingLevel,
)
from app.core.models import UUIDMixin


class Pathway(UUIDMixin, Base):
    """A phân luồng route after a schooling stage (FR-31, FR-62).

    Reference data. ``type`` covers the academic track and the three
    non-academic branches — including the GDNN / vocational-secondary route
    that career profiles must be able to surface.
    """

    __tablename__ = "pathway"
    __table_args__ = (Index("ix_pathway_type", "type"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[PathwayType] = mapped_column(Enum(PathwayType), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")


class CareerProfile(UUIDMixin, Base):
    """A public occupation profile (Điều 5(a), FR-30..33).

    ``riasec_codes`` and ``required_competencies`` are comma-joined strings for
    SQLite/Postgres portability (mirrors ``Competency.dieu5_codes``); the schema
    layer splits them to lists. Content is versioned (FR-33): updating a profile
    means bumping ``version`` and ``source_ref``, never silently mutating.
    """

    __tablename__ = "career_profile"
    __table_args__ = (
        Index("ix_career_profile_field", "field"),
        Index("ix_career_profile_training_level", "training_level"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # Coarse occupational field/lĩnh vực (e.g. "technology", "health"); filterable.
    field: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    # Comma-joined RIASEC letters (e.g. "I,R"); schema layer splits to a list.
    riasec_codes: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    # Comma-joined competency codes (NL1..NL12).
    required_competencies: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    training_level: Mapped[TrainingLevel] = mapped_column(Enum(TrainingLevel), nullable=False)
    training_paths: Mapped[str] = mapped_column(Text, nullable=False, default="")
    labor_market_outlook: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Constant per spec.md §5 (CareerProfile.dieu5_code='a').
    dieu5_code: Mapped[str] = mapped_column(String(8), nullable=False, default="a")

    pathways: Mapped[list[Pathway]] = relationship(secondary="career_pathway", lazy="selectin")


class CareerPathway(UUIDMixin, Base):
    """Join row linking a ``CareerProfile`` to a ``Pathway`` (many-to-many)."""

    __tablename__ = "career_pathway"
    __table_args__ = (
        Index("ix_career_pathway_pathway", "pathway_id"),
        Index("ix_career_pathway_career_pathway", "career_id", "pathway_id", unique=True),
    )

    career_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("career_profile.id", ondelete="CASCADE"), nullable=False
    )
    pathway_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("pathway.id", ondelete="CASCADE"), nullable=False
    )


class ContentItem(UUIDMixin, Base):
    """A versioned unit of public career-selection / experience content (5c/5d).

    Tagged on both axes (ADR-013): ``dieu5_code`` (legal) + ``competency_code``
    (pedagogical), plus ``depth`` + ``dev_phase`` + ``school_level`` + publication
    ``status``. Versioned (FR-90, NFR-26): a content change is a new version.
    """

    __tablename__ = "content_item"
    __table_args__ = (
        Index(
            "ix_content_item_filters",
            "dieu5_code",
            "competency_code",
            "dev_phase",
            "school_level",
        ),
        Index("ix_content_item_status", "status"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    dieu5_code: Mapped[str] = mapped_column(String(8), nullable=False)
    competency_code: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    depth: Mapped[Depth | None] = mapped_column(Enum(Depth), nullable=True)
    dev_phase: Mapped[DevPhase | None] = mapped_column(Enum(DevPhase), nullable=True)
    school_level: Mapped[SchoolLevel | None] = mapped_column(Enum(SchoolLevel), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), nullable=False, default=ContentStatus.PUBLISHED
    )
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False, default="")
