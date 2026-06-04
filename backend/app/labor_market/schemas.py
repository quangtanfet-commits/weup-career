"""Pydantic schemas for the Labor Market Intelligence API (spec.md §6, FR-34/FR-35)."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from app.labor_market.models import LaborMarketSnapshot
from app.labor_market.service import LmiStatus


def _split(codes: str) -> list[str]:
    """Split a comma-joined skill string into a clean list."""
    return [c for c in (part.strip() for part in codes.split(",")) if c]


class LaborMarketSnapshotOut(BaseModel):
    """API output for a single LaborMarketSnapshot (FR-34)."""

    id: str
    sector: str
    region: str
    salary_range: str
    demand_forecast: str
    required_skills: list[str]
    source_ref: str
    as_of_date: date
    version: int

    @classmethod
    def from_model(cls, snap: LaborMarketSnapshot) -> LaborMarketSnapshotOut:
        return cls(
            id=snap.id,
            sector=snap.sector,
            region=snap.region,
            salary_range=snap.salary_range,
            demand_forecast=snap.demand_forecast,
            required_skills=_split(snap.required_skills),
            source_ref=snap.source_ref,
            as_of_date=snap.as_of_date,
            version=snap.version,
        )


class LmiStatusOut(BaseModel):
    """Embedded LMI status for a career detail response (FR-35).

    ``status`` is one of: "available" | "stale" | "no_data".
    When "stale" or "no_data", the UI must display "chưa có dữ liệu TTLĐ".
    """

    status: LmiStatus
