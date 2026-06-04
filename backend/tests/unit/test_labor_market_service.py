"""Labor Market Intelligence service unit tests (FR-34, FR-35).

Tests the service layer directly against an in-memory SQLite DB — covers
provenance validation, repository behaviour, and the LMI status logic without
HTTP overhead. These run fast and cover the business-logic path that integration
tests exercise via the router.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from app.core.exceptions import ValidationError
from app.labor_market.repository import SqlLaborMarketRepo
from app.labor_market.service import LaborMarketService, SnapshotDraft
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


# -- helpers ---------------------------------------------------------------


async def _make_service(session: AsyncSession) -> LaborMarketService:
    repo = SqlLaborMarketRepo(session)
    return LaborMarketService(repo=repo)


# -- Seed produces no rows -------------------------------------------------


async def test_seed_creates_zero_rows(db: object) -> None:
    """The seed function must insert zero rows (no fabricated data)."""
    from app.labor_market.seed import seed_labor_market

    db_ = db  # type: ignore[assignment]
    async with db_.session_factory() as s:  # type: ignore[attr-defined]
        count = await seed_labor_market(s)
        await s.commit()
    assert count == 0, f"seed should insert 0 rows, got {count}"


# -- Repository list -------------------------------------------------------


async def test_repo_list_empty(session: AsyncSession) -> None:
    """list_snapshots returns empty list when table is empty."""
    repo = SqlLaborMarketRepo(session)
    result = await repo.list_snapshots()
    assert result == []


async def test_repo_list_returns_fresh(session: AsyncSession) -> None:
    """list_snapshots returns fresh snapshot rows."""
    from app.core.models import new_uuid
    from app.labor_market.models import LaborMarketSnapshot

    snap = LaborMarketSnapshot(
        id=new_uuid(),
        sector="technology",
        region="toàn quốc",
        salary_range="20-40M",
        demand_forecast="tăng",
        required_skills="Python,SQL",
        source_ref="ILO VN 2024",
        as_of_date=date.today(),
        version=1,
    )
    session.add(snap)
    await session.flush()

    repo = SqlLaborMarketRepo(session)
    result = await repo.list_snapshots()
    assert len(result) == 1
    assert result[0].sector == "technology"


async def test_repo_list_excludes_stale(session: AsyncSession) -> None:
    """list_snapshots excludes rows whose as_of_date is beyond the staleness threshold."""
    from app.core.models import new_uuid
    from app.labor_market.models import LaborMarketSnapshot

    stale = LaborMarketSnapshot(
        id=new_uuid(),
        sector="engineering",
        region="toàn quốc",
        salary_range="15-25M",
        demand_forecast="ổn định",
        required_skills="AutoCAD",
        source_ref="ILO VN 2022",
        as_of_date=date.today() - timedelta(days=400),
        version=1,
    )
    session.add(stale)
    await session.flush()

    repo = SqlLaborMarketRepo(session)
    result = await repo.list_snapshots()
    assert result == []


async def test_repo_filter_by_sector(session: AsyncSession) -> None:
    """list_snapshots(sector=...) filters by sector."""
    from app.core.models import new_uuid
    from app.labor_market.models import LaborMarketSnapshot

    for s_name in ("technology", "health"):
        session.add(
            LaborMarketSnapshot(
                id=new_uuid(),
                sector=s_name,
                region="toàn quốc",
                salary_range="10-20M",
                demand_forecast="tăng",
                required_skills="Python",
                source_ref="ILO 2024",
                as_of_date=date.today(),
                version=1,
            )
        )
    await session.flush()

    repo = SqlLaborMarketRepo(session)
    result = await repo.list_snapshots(sector="technology")
    assert len(result) == 1
    assert result[0].sector == "technology"


async def test_repo_filter_by_region(session: AsyncSession) -> None:
    """list_snapshots(region=...) filters by region."""
    from app.core.models import new_uuid
    from app.labor_market.models import LaborMarketSnapshot

    for region in ("Hà Nội", "Hồ Chí Minh"):
        session.add(
            LaborMarketSnapshot(
                id=new_uuid(),
                sector="technology",
                region=region,
                salary_range="15-30M",
                demand_forecast="tăng",
                required_skills="Python",
                source_ref="ILO 2024",
                as_of_date=date.today(),
                version=1,
            )
        )
    await session.flush()

    repo = SqlLaborMarketRepo(session)
    result = await repo.list_snapshots(region="Hà Nội")
    assert len(result) == 1
    assert result[0].region == "Hà Nội"


# -- Service provenance validation ----------------------------------------


async def test_service_rejects_empty_source_ref(session: AsyncSession) -> None:
    """Service raises ValidationError when source_ref is empty."""
    svc = await _make_service(session)
    draft = SnapshotDraft(
        sector="technology",
        region="toàn quốc",
        salary_range="20-40M",
        demand_forecast="tăng",
        required_skills=["Python"],
        source_ref="",  # empty — should be rejected
        as_of_date=date.today(),
    )
    with pytest.raises(ValidationError):
        await svc.create_snapshot(draft)


async def test_service_rejects_future_as_of_date(session: AsyncSession) -> None:
    """Service raises ValidationError when as_of_date is in the future."""
    svc = await _make_service(session)
    draft = SnapshotDraft(
        sector="technology",
        region="toàn quốc",
        salary_range="20-40M",
        demand_forecast="tăng",
        required_skills=["Python"],
        source_ref="ILO VN 2024",
        as_of_date=date.today() + timedelta(days=1),
    )
    with pytest.raises(ValidationError):
        await svc.create_snapshot(draft)


async def test_service_create_valid_snapshot(session: AsyncSession) -> None:
    """Service creates a valid snapshot and returns it."""
    svc = await _make_service(session)
    draft = SnapshotDraft(
        sector="technology",
        region="toàn quốc",
        salary_range="20-40M",
        demand_forecast="tăng mạnh",
        required_skills=["Python", "SQL"],
        source_ref="ILO VN 2024",
        as_of_date=date.today(),
    )
    snap = await svc.create_snapshot(draft)
    assert snap.sector == "technology"
    assert snap.source_ref == "ILO VN 2024"
    assert snap.required_skills == "Python,SQL"


# -- LMI status logic ------------------------------------------------------


async def test_lmi_status_no_data_when_empty(session: AsyncSession) -> None:
    """lmi_status_for_sector returns 'no_data' when no snapshot exists."""
    svc = await _make_service(session)
    status = await svc.lmi_status_for_sector("technology")
    assert status == "no_data"


async def test_lmi_status_available_when_fresh(session: AsyncSession) -> None:
    """lmi_status_for_sector returns 'available' when a fresh snapshot exists."""
    from app.core.models import new_uuid
    from app.labor_market.models import LaborMarketSnapshot

    session.add(
        LaborMarketSnapshot(
            id=new_uuid(),
            sector="technology",
            region="toàn quốc",
            salary_range="20-40M",
            demand_forecast="tăng",
            required_skills="Python",
            source_ref="ILO 2024",
            as_of_date=date.today(),
            version=1,
        )
    )
    await session.flush()
    svc = await _make_service(session)
    status = await svc.lmi_status_for_sector("technology")
    assert status == "available"


async def test_lmi_status_stale_when_old(session: AsyncSession) -> None:
    """lmi_status_for_sector returns 'stale' when only old snapshots exist."""
    from app.core.models import new_uuid
    from app.labor_market.models import LaborMarketSnapshot

    session.add(
        LaborMarketSnapshot(
            id=new_uuid(),
            sector="engineering",
            region="toàn quốc",
            salary_range="15-25M",
            demand_forecast="ổn định",
            required_skills="AutoCAD",
            source_ref="ILO 2020",
            as_of_date=date.today() - timedelta(days=400),
            version=1,
        )
    )
    await session.flush()
    svc = await _make_service(session)
    status = await svc.lmi_status_for_sector("engineering")
    assert status == "stale"
