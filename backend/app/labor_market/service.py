"""LaborMarketService — structured LMI with provenance enforcement (FR-34/FR-35).

Pure business logic, no FastAPI imports (hexagonal, ADR-009).

**Provenance validation (ADR-015 §Decision 2):**
- ``source_ref`` MUST be non-empty — validated here as defence-in-depth after the
  NOT-NULL schema constraint.
- ``as_of_date`` MUST NOT be in the future — a future date is a data-quality error.

**LMI status (FR-35):**
``lmi_status_for_sector`` returns one of three states:
- ``"available"`` — a fresh (non-stale) snapshot exists for the sector.
- ``"stale"`` — a snapshot exists but all are beyond the 365-day threshold.
- ``"no_data"`` — no snapshot at all for that sector.

The UI must display "chưa có dữ liệu TTLĐ" for ``stale`` or ``no_data`` (FR-35).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.core.exceptions import ValidationError
from app.core.models import new_uuid
from app.labor_market.models import LaborMarketSnapshot
from app.labor_market.repository import ILaborMarketRepo

LmiStatus = Literal["available", "stale", "no_data"]


@dataclass(frozen=True)
class SnapshotDraft:
    """Caller-supplied fields for a new LaborMarketSnapshot.

    All fields are mandatory. ``required_skills`` is supplied as a list and
    converted to the comma-joined String convention internally.
    """

    sector: str
    region: str
    salary_range: str
    demand_forecast: str
    required_skills: list[str]
    source_ref: str  # MANDATORY — provenance guard
    as_of_date: date  # MANDATORY — data timestamp
    version: int = 1


class LaborMarketService:
    def __init__(self, *, repo: ILaborMarketRepo) -> None:
        self._repo = repo

    async def list_snapshots(
        self,
        *,
        sector: str | None = None,
        region: str | None = None,
    ) -> list[LaborMarketSnapshot]:
        """Return fresh non-stale snapshots, optionally filtered (FR-34).

        Returns an empty list cleanly when no data exists — never raises.
        """
        return await self._repo.list_snapshots(sector=sector, region=region)

    async def create_snapshot(self, draft: SnapshotDraft) -> LaborMarketSnapshot:
        """Create a snapshot with mandatory provenance validation.

        Raises ``ValidationError`` (422) when:
        - ``source_ref`` is empty (ADR-015 provenance guard).
        - ``as_of_date`` is in the future (data-quality guard).
        """
        if not draft.source_ref.strip():
            raise ValidationError(
                "source_ref là bắt buộc — mọi snapshot phải có nguồn thẩm quyền",
                details={"field": "source_ref"},
            )
        if draft.as_of_date > date.today():
            raise ValidationError(
                "as_of_date không được là ngày tương lai",
                details={"field": "as_of_date"},
            )
        snap = LaborMarketSnapshot(
            id=new_uuid(),
            sector=draft.sector,
            region=draft.region,
            salary_range=draft.salary_range,
            demand_forecast=draft.demand_forecast,
            required_skills=",".join(draft.required_skills),
            source_ref=draft.source_ref,
            as_of_date=draft.as_of_date,
            version=draft.version,
        )
        return await self._repo.add_snapshot(snap)

    async def lmi_status_for_sector(self, sector: str) -> LmiStatus:
        """Return the LMI status for a given sector (FR-35).

        - ``"available"`` — a fresh snapshot exists (within 365 days).
        - ``"stale"``    — a snapshot exists but is beyond the threshold.
        - ``"no_data"``  — no snapshot at all.

        Callers (e.g. the careers router for FR-35) use this to decide the
        ``lmi_status`` field on CareerDetailOut without loading full snapshot data.
        """
        fresh = await self._repo.fresh_snapshot_for_sector(sector)
        if fresh is not None:
            return "available"
        any_snap = await self._repo.any_snapshot_for_sector(sector)
        if any_snap is not None:
            return "stale"
        return "no_data"
