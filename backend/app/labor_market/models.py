"""Labor Market Intelligence ORM model (spec.md §5, FR-34/FR-35; ADR-015).

``LaborMarketSnapshot`` is the structured representation of labor market data for
a given sector × region combination. It is the first-class entity that replaces
the free-text ``CareerProfile.labor_market_outlook`` for quantitative signals.

**Provenance guard (ADR-015 §Decision 2):**
``source_ref`` and ``as_of_date`` are NOT NULL at the schema level — no snapshot
may be created without citing an authoritative source and the data timestamp.
This is the hard fence against inserting unverified figures.

**Staleness:** callers filter on ``as_of_date`` relative to a threshold (365 days
by default, NFR-26); the model itself does not embed the staleness logic —
that belongs in the service.

**required_skills:** comma-joined String per project convention (SQLite/Postgres
portability — mirrors ``CareerProfile.riasec_codes``).

**Sector join:** ``CareerProfile`` is linked to ``LaborMarketSnapshot`` by matching
``CareerProfile.field == LaborMarketSnapshot.sector`` at query time (no FK column).
This avoids a migration touching the existing ``career_profile`` table.

This module is **not consent-gated** (CP-1..CP-8 untouched).
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.models import UUIDMixin, new_uuid, utcnow


class LaborMarketSnapshot(UUIDMixin, Base):
    """A structured LMI snapshot for one sector × region pair.

    ``source_ref`` and ``as_of_date`` are NOT NULL — provenance is mandatory.
    """

    __tablename__ = "labor_market_snapshot"
    __table_args__ = (
        Index("ix_lms_sector", "sector"),
        Index("ix_lms_region", "region"),
        Index("ix_lms_sector_region", "sector", "region"),
    )

    # Occupational sector (e.g. "technology", "health"). Join key to CareerProfile.field.
    sector: Mapped[str] = mapped_column(String(128), nullable=False)
    # Human-readable salary band (e.g. "15–30 triệu VNĐ/tháng").
    salary_range: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    # Demand direction label (e.g. "tăng mạnh", "ổn định").
    demand_forecast: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    # Comma-joined required skill labels (project convention — no Postgres ARRAY).
    required_skills: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    # Geographic scope (e.g. "toàn quốc", "Hà Nội").
    region: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    # PROVENANCE GUARD — NOT NULL by design (ADR-015).
    source_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    # DATA TIMESTAMP — NOT NULL by design (ADR-015); used for staleness checks.
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    # Content version; bump when the snapshot is superseded.
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # Row creation timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
