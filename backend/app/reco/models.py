"""Recommendation ORM model (spec.md §5, FR-60..63, ADR-012, CP-5/CP-6).

A ``Recommendation`` is an explainable, human-in-the-loop career/pathway
suggestion produced by the deterministic engine (``app.reco.engine``):

- ``payload`` — JSON: the ranked careers + suggested pathway + their scores.
- ``rationale`` — human-readable Vietnamese explanation. **DB-level NOT NULL**
  (``nullable=False`` with no default): the database itself forbids a
  rationale-less recommendation, which is the storage-layer half of CP-6
  (the service guard is the other half — defence in depth).
- ``requires_human_confirmation`` — defaults ``True``. A recommendation starts
  *proposed* and is **not effective** until a person confirms it (CP-5).
- ``confirmed_by`` / ``confirmed_decision`` — written ONLY by a human via
  ``confirm`` (the owner / guardian / counselor). The system never sets them
  itself (CP-5, human-in-the-loop).

Recommendations are derived from a learner's sensitive profile, so the route
that creates them is consent-gated (CP-1) like assessments/progress. The stored
``payload`` carries career/pathway ids + scores + rationale — no raw assessment
result content (that stays encrypted in ``AssessmentResult``).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import RecoDecision
from app.core.models import UUIDMixin, utcnow


class Recommendation(UUIDMixin, Base):
    """An explainable, human-in-the-loop recommendation (FR-60..63, CP-5/CP-6)."""

    __tablename__ = "recommendation"
    __table_args__ = (
        Index("ix_recommendation_user", "user_id"),
        Index("ix_recommendation_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
    )
    # The suggested careers/pathways + scores (JSON). Portable across SQLite/PG.
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    # CP-6: rationale is NOT NULL at the DB level — no default, so a row without
    # one cannot be inserted. The service also guards against empty/whitespace.
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_confirmation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Human-in-the-loop (CP-5): set ONLY by a person via confirm(). nullable.
    confirmed_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_decision: Mapped[RecoDecision | None] = mapped_column(
        Enum(RecoDecision), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
