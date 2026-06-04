"""Labor Market Intelligence HTTP routes (spec.md §6, FR-34/FR-35).

``GET /labor-market/snapshots`` — structured LMI endpoint (FR-34).

**Auth:** Bearer required (unlike the public career library). LMI data is
operational content for careers guidance — not anonymous-readable like Điều-5(a)
public career profiles.

**Empty state:** returns ``[]`` cleanly when no snapshot data exists. This is the
expected MVP state (seed creates zero rows per ADR-015). The frontend must handle
this gracefully rather than showing an error.

**Staleness:** stale snapshots (as_of_date > 365 days) are excluded by the
repository; the endpoint does not return stale data.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_current_user, get_session
from app.labor_market.repository import SqlLaborMarketRepo
from app.labor_market.schemas import LaborMarketSnapshotOut
from app.labor_market.service import LaborMarketService

router = APIRouter(tags=["labor-market"])


def _labor_market_service(session: AsyncSession = Depends(get_session)) -> LaborMarketService:
    return LaborMarketService(repo=SqlLaborMarketRepo(session))


@router.get("/labor-market/snapshots", response_model=list[LaborMarketSnapshotOut])
async def list_snapshots(
    sector: str | None = Query(None, description="Lọc theo ngành (sector)"),
    region: str | None = Query(None, description="Lọc theo vùng (region)"),
    _current: CurrentUser = Depends(get_current_user),
    service: LaborMarketService = Depends(_labor_market_service),
) -> list[LaborMarketSnapshotOut]:
    """List fresh LMI snapshots, optionally filtered by sector and/or region.

    Returns ``[]`` when no data exists (FR-34 — empty state is not an error).
    Stale snapshots (older than 365 days) are excluded.
    """
    snaps = await service.list_snapshots(sector=sector, region=region)
    return [LaborMarketSnapshotOut.from_model(s) for s in snaps]
