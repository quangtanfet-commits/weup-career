"""Tests for the instrument seed loader (gap G-1): production-runnable,
idempotent seeding so a fresh DB can serve submit/read (not just test fixtures)."""

from __future__ import annotations

import pytest
from app.assessments.models import AssessmentInstrument, AssessmentItem
from app.assessments.seed import ITEMS_BY_TYPE, seed_instruments
from app.core.database import Database
from app.core.enums import InstrumentType
from sqlalchemy import func, select


async def _count(db: Database, model: type) -> int:
    async with db.session_factory() as s:
        return int((await s.execute(select(func.count()).select_from(model))).scalar_one())


@pytest.mark.asyncio
async def test_seed_creates_one_active_instrument_per_type(db: Database) -> None:
    async with db.session_factory() as s:
        ids = await seed_instruments(s)
        await s.commit()

    assert sorted(ids) == ["mbti", "riasec", "vips"]
    assert await _count(db, AssessmentInstrument) == len(InstrumentType)
    # Every instrument is active and carries its full item bank.
    expected_items = sum(len(v) for v in ITEMS_BY_TYPE.values())
    assert await _count(db, AssessmentItem) == expected_items
    async with db.session_factory() as s:
        rows = (await s.execute(select(AssessmentInstrument))).scalars().all()
        assert all(r.is_active for r in rows)


@pytest.mark.asyncio
async def test_seed_is_idempotent(db: Database) -> None:
    async with db.session_factory() as s:
        first = await seed_instruments(s)
        await s.commit()
    async with db.session_factory() as s:
        second = await seed_instruments(s)  # re-run on an already-seeded DB
        await s.commit()

    assert first == second  # same instrument ids, no duplicates
    assert await _count(db, AssessmentInstrument) == len(InstrumentType)
    expected_items = sum(len(v) for v in ITEMS_BY_TYPE.values())
    assert await _count(db, AssessmentItem) == expected_items
