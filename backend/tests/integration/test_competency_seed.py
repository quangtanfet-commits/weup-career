"""Competency seed loader tests (FR-20/21): 12 competencies + indicators, idempotent."""

from __future__ import annotations

import pytest
from app.competency.models import Competency, Indicator
from app.competency.seed import COMPETENCIES, seed_competencies
from app.core.database import Database
from app.core.enums import CompetencyArea, Depth
from sqlalchemy import func, select


async def _count(db: Database, model: type) -> int:
    async with db.session_factory() as s:
        return int((await s.execute(select(func.count()).select_from(model))).scalar_one())


@pytest.mark.asyncio
async def test_seed_creates_twelve_competencies(db: Database) -> None:
    async with db.session_factory() as s:
        ids = await seed_competencies(s)
        await s.commit()

    assert len(ids) == 12
    assert await _count(db, Competency) == 12
    # Three indicators (K/A/R) per competency.
    assert await _count(db, Indicator) == 12 * 3


@pytest.mark.asyncio
async def test_seed_codes_and_areas(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_competencies(s)
        await s.commit()
        rows = (await s.execute(select(Competency))).scalars().all()

    codes = {r.code for r in rows}
    assert codes == {f"NL{i}" for i in range(1, 13)}
    # Four competencies per area (A/B/C).
    by_area: dict[CompetencyArea, int] = dict.fromkeys(CompetencyArea, 0)
    for r in rows:
        by_area[r.area] += 1
    assert by_area == {
        CompetencyArea.A_PERSONAL: 4,
        CompetencyArea.B_EXPLORATION: 4,
        CompetencyArea.C_BUILDING: 4,
    }


@pytest.mark.asyncio
async def test_seed_indicator_depths_each_competency(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_competencies(s)
        await s.commit()
        comps = (await s.execute(select(Competency))).scalars().all()
        for comp in comps:
            inds = (
                (await s.execute(select(Indicator).where(Indicator.competency_id == comp.id)))
                .scalars()
                .all()
            )
            assert {i.depth for i in inds} == {Depth.K, Depth.A, Depth.R}


@pytest.mark.asyncio
async def test_seed_is_idempotent(db: Database) -> None:
    async with db.session_factory() as s:
        first = await seed_competencies(s)
        await s.commit()
    async with db.session_factory() as s:
        second = await seed_competencies(s)  # re-run on already-seeded DB
        await s.commit()

    assert first == second  # same ids, no duplicates
    assert await _count(db, Competency) == 12
    assert await _count(db, Indicator) == 36


def test_seed_table_dieu5_nonempty() -> None:
    # Every competency in the static table carries at least one Điều 5 code.
    assert all(len(dieu5) >= 1 for _, _, _, _, dieu5 in COMPETENCIES)
