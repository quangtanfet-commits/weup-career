"""Labor Market Intelligence API integration tests (FR-34, FR-35; ADR-015).

This module tests the new ``app/labor_market/`` slice end-to-end via the HTTP
layer. Key invariants:

- Empty list is returned cleanly when no snapshot data exists (FR-34).
- ``source_ref`` and ``as_of_date`` are provenance guards at the schema level:
  a snapshot without them is rejected (ADR-015 Decision §2).
- Stale snapshots (``as_of_date`` > 365 days old) are excluded from results.
- The careers list gains ``lmi_status`` ("available" | "stale" | "no_data")
  for each career when labor market data is requested (FR-35).
- ``sort_by_demand=true`` floats careers with fresh LMI data to the top.

These are real DB tests (no mocks) — coverage counts.
"""

from __future__ import annotations

import pytest
from datetime import date, timedelta
from app.core.database import Database
from httpx import AsyncClient

from tests.conftest import mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio


# -- helpers ---------------------------------------------------------------


async def _adult_token(client: AsyncClient, email: str = "lmi_adult@example.com") -> str:
    resp = await register_and_verify(client, mailer_of(client), email=email, dob="1990-01-01")
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Password123"}
    )
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_snapshot(
    db: Database,
    *,
    sector: str = "technology",
    region: str = "toàn quốc",
    salary_range: str = "20-40 triệu VNĐ",
    demand_forecast: str = "tăng mạnh",
    required_skills: str = "Python,SQL",
    source_ref: str = "ILO VN 2024",
    as_of_date: date | None = None,
    version: int = 1,
) -> str:
    """Insert a LaborMarketSnapshot directly into the DB; return its id."""
    from app.labor_market.models import LaborMarketSnapshot
    from app.core.models import new_uuid

    snap_id = new_uuid()
    effective_date = as_of_date if as_of_date is not None else date.today()
    async with db.session_factory() as s:
        s.add(
            LaborMarketSnapshot(
                id=snap_id,
                sector=sector,
                region=region,
                salary_range=salary_range,
                demand_forecast=demand_forecast,
                required_skills=required_skills,
                source_ref=source_ref,
                as_of_date=effective_date,
                version=version,
            )
        )
        await s.commit()
    return snap_id


# -- GET /api/v1/labor-market/snapshots ------------------------------------


async def test_list_snapshots_empty_when_no_data(
    client: AsyncClient, db: Database
) -> None:
    """Empty list returned cleanly when no snapshot exists (FR-34 — no error)."""
    token = await _adult_token(client)
    resp = await client.get("/api/v1/labor-market/snapshots", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_snapshots_returns_fresh_snapshot(
    client: AsyncClient, db: Database
) -> None:
    """A freshly-dated snapshot is returned in the list."""
    token = await _adult_token(client, "lmi_fresh@example.com")
    await _create_snapshot(db, sector="health", region="Hà Nội")
    resp = await client.get("/api/v1/labor-market/snapshots", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    snap = body[0]
    assert snap["sector"] == "health"
    assert snap["region"] == "Hà Nội"
    assert snap["source_ref"] == "ILO VN 2024"
    assert "as_of_date" in snap
    assert "required_skills" in snap


async def test_list_snapshots_filter_by_sector(
    client: AsyncClient, db: Database
) -> None:
    """Only snapshots matching the requested sector are returned."""
    token = await _adult_token(client, "lmi_sec@example.com")
    await _create_snapshot(db, sector="technology", region="toàn quốc")
    await _create_snapshot(db, sector="health", region="toàn quốc")
    resp = await client.get(
        "/api/v1/labor-market/snapshots",
        params={"sector": "technology"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["sector"] == "technology"


async def test_list_snapshots_filter_by_region(
    client: AsyncClient, db: Database
) -> None:
    """Only snapshots matching the requested region are returned."""
    token = await _adult_token(client, "lmi_reg@example.com")
    await _create_snapshot(db, sector="technology", region="Hà Nội")
    await _create_snapshot(db, sector="technology", region="Hồ Chí Minh")
    resp = await client.get(
        "/api/v1/labor-market/snapshots",
        params={"region": "Hà Nội"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["region"] == "Hà Nội"


async def test_list_snapshots_excludes_stale(
    client: AsyncClient, db: Database
) -> None:
    """Snapshots older than 365 days are excluded (NFR-26 / ADR-015 cadence)."""
    token = await _adult_token(client, "lmi_stale@example.com")
    stale_date = date.today() - timedelta(days=366)
    await _create_snapshot(db, sector="engineering", as_of_date=stale_date)
    resp = await client.get(
        "/api/v1/labor-market/snapshots",
        params={"sector": "engineering"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_snapshots_requires_auth(client: AsyncClient, db: Database) -> None:
    """Unauthenticated request returns 401 (unlike public career library)."""
    resp = await client.get("/api/v1/labor-market/snapshots")
    assert resp.status_code == 401


# -- Provenance rejection ---------------------------------------------------


async def test_provenance_rejection_missing_source_ref(
    client: AsyncClient, db: Database
) -> None:
    """A snapshot insert without source_ref is rejected at the DB/schema level."""
    from app.labor_market.models import LaborMarketSnapshot
    from app.core.models import new_uuid
    from sqlalchemy.exc import IntegrityError

    async with db.session_factory() as s:
        s.add(
            LaborMarketSnapshot(
                id=new_uuid(),
                sector="tech",
                region="toàn quốc",
                salary_range="10-20M",
                demand_forecast="ổn định",
                required_skills="Python",
                source_ref=None,  # type: ignore[arg-type]
                as_of_date=date.today(),
                version=1,
            )
        )
        with pytest.raises((IntegrityError, Exception)):
            await s.commit()


async def test_provenance_rejection_missing_as_of_date(
    client: AsyncClient, db: Database
) -> None:
    """A snapshot insert without as_of_date is rejected at the DB/schema level."""
    from app.labor_market.models import LaborMarketSnapshot
    from app.core.models import new_uuid
    from sqlalchemy.exc import IntegrityError

    async with db.session_factory() as s:
        s.add(
            LaborMarketSnapshot(
                id=new_uuid(),
                sector="tech",
                region="toàn quốc",
                salary_range="10-20M",
                demand_forecast="ổn định",
                required_skills="Python",
                source_ref="ILO VN 2024",
                as_of_date=None,  # type: ignore[arg-type]
                version=1,
            )
        )
        with pytest.raises((IntegrityError, Exception)):
            await s.commit()


# -- FR-35: Career LMI status ----------------------------------------------


async def test_career_detail_lmi_status_no_data(
    client: AsyncClient, db: Database, seeded_careers: dict[str, int]
) -> None:
    """Career detail shows lmi_status='no_data' when no matching snapshot exists."""
    token = await _adult_token(client, "lmi_nodata@example.com")
    resp = await client.get("/api/v1/careers", headers=_auth(token))
    assert resp.status_code == 200
    careers = resp.json()
    assert len(careers) > 0
    # GET detail for the first career
    career_id = careers[0]["id"]
    resp = await client.get(f"/api/v1/careers/{career_id}", headers=_auth(token))
    assert resp.status_code == 200
    detail = resp.json()
    # lmi_status must be present and signal no data
    assert "lmi_status" in detail
    assert detail["lmi_status"] == "no_data"


async def test_career_detail_lmi_status_available(
    client: AsyncClient, db: Database, seeded_careers: dict[str, int]
) -> None:
    """Career detail shows lmi_status='available' when a fresh snapshot exists."""
    token = await _adult_token(client, "lmi_avail@example.com")
    # Find a seeded career and its sector (field)
    resp = await client.get("/api/v1/careers", headers=_auth(token))
    careers = resp.json()
    career = next(c for c in careers if c["field"] == "technology")
    # Insert a fresh snapshot matching that sector
    await _create_snapshot(db, sector="technology", region="toàn quốc")
    resp = await client.get(f"/api/v1/careers/{career['id']}", headers=_auth(token))
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["lmi_status"] == "available"


async def test_career_detail_lmi_status_stale(
    client: AsyncClient, db: Database, seeded_careers: dict[str, int]
) -> None:
    """Career detail shows lmi_status='stale' when only old snapshot exists."""
    token = await _adult_token(client, "lmi_stalec@example.com")
    resp = await client.get("/api/v1/careers", headers=_auth(token))
    careers = resp.json()
    career = next(c for c in careers if c["field"] == "health")
    stale_date = date.today() - timedelta(days=400)
    await _create_snapshot(db, sector="health", as_of_date=stale_date)
    resp = await client.get(f"/api/v1/careers/{career['id']}", headers=_auth(token))
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["lmi_status"] == "stale"


async def test_careers_sort_by_demand_puts_lmi_careers_first(
    client: AsyncClient, db: Database, seeded_careers: dict[str, int]
) -> None:
    """sort_by_demand=true brings careers with fresh LMI data to the front."""
    token = await _adult_token(client, "lmi_sort@example.com")
    # Insert snapshot for 'technology' only
    await _create_snapshot(db, sector="technology", region="toàn quốc")
    resp = await client.get(
        "/api/v1/careers",
        params={"sort_by_demand": "true"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    careers = resp.json()
    assert len(careers) > 0
    # First career should be the one with LMI data
    first_career = careers[0]
    assert first_career["field"] == "technology"
