"""Labor Market Intelligence repository — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.

Staleness is enforced here at the data layer: ``list_snapshots`` filters out rows
whose ``as_of_date`` is older than ``STALE_THRESHOLD_DAYS`` (365). This keeps the
staleness logic co-located with the query rather than scattered across callers.

``any_snapshot_for_sector`` (used by the careers LMI-status query) queries ALL
rows including stale, so the service can distinguish "no data" vs "stale".
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.labor_market.models import LaborMarketSnapshot

STALE_THRESHOLD_DAYS = 365


def _stale_cutoff() -> date:
    return date.today() - timedelta(days=STALE_THRESHOLD_DAYS)


class ILaborMarketRepo(Protocol):
    async def list_snapshots(
        self,
        *,
        sector: str | None = None,
        region: str | None = None,
    ) -> list[LaborMarketSnapshot]:
        """Return fresh (non-stale) snapshots, optionally filtered."""
        ...

    async def any_snapshot_for_sector(self, sector: str) -> LaborMarketSnapshot | None:
        """Return the most-recent snapshot for the sector (any age), or None."""
        ...

    async def fresh_snapshot_for_sector(self, sector: str) -> LaborMarketSnapshot | None:
        """Return the most-recent fresh snapshot for the sector, or None."""
        ...

    async def add_snapshot(self, snap: LaborMarketSnapshot) -> LaborMarketSnapshot:
        ...


class SqlLaborMarketRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_snapshots(
        self,
        *,
        sector: str | None = None,
        region: str | None = None,
    ) -> list[LaborMarketSnapshot]:
        """Return fresh snapshots ordered by sector then as_of_date desc."""
        cutoff = _stale_cutoff()
        stmt = (
            select(LaborMarketSnapshot)
            .where(LaborMarketSnapshot.as_of_date >= cutoff)
            .order_by(LaborMarketSnapshot.sector, LaborMarketSnapshot.as_of_date.desc())
        )
        if sector is not None:
            stmt = stmt.where(LaborMarketSnapshot.sector == sector)
        if region is not None:
            stmt = stmt.where(LaborMarketSnapshot.region == region)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def any_snapshot_for_sector(self, sector: str) -> LaborMarketSnapshot | None:
        """Most-recent snapshot for the sector regardless of staleness."""
        stmt = (
            select(LaborMarketSnapshot)
            .where(LaborMarketSnapshot.sector == sector)
            .order_by(LaborMarketSnapshot.as_of_date.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def fresh_snapshot_for_sector(self, sector: str) -> LaborMarketSnapshot | None:
        """Most-recent fresh (non-stale) snapshot for the sector."""
        cutoff = _stale_cutoff()
        stmt = (
            select(LaborMarketSnapshot)
            .where(
                LaborMarketSnapshot.sector == sector,
                LaborMarketSnapshot.as_of_date >= cutoff,
            )
            .order_by(LaborMarketSnapshot.as_of_date.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def add_snapshot(self, snap: LaborMarketSnapshot) -> LaborMarketSnapshot:
        self._session.add(snap)
        await self._session.flush()
        return snap
