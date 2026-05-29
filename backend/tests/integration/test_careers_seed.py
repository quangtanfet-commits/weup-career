"""Careers seed loader tests (FR-30..33/40..42/50..51): pathways + careers + content, idempotent."""

from __future__ import annotations

import pytest
from app.careers.models import CareerPathway, CareerProfile, ContentItem, Pathway
from app.careers.seed import CAREERS, CONTENT, PATHWAYS, seed_careers
from app.core.database import Database
from app.core.enums import ContentStatus, PathwayType
from sqlalchemy import func, select


async def _count(db: Database, model: type) -> int:
    async with db.session_factory() as s:
        return int((await s.execute(select(func.count()).select_from(model))).scalar_one())


@pytest.mark.asyncio
async def test_seed_creates_pathways_careers_content(db: Database) -> None:
    async with db.session_factory() as s:
        counts = await seed_careers(s)
        await s.commit()

    assert counts == {"pathways": len(PATHWAYS), "careers": len(CAREERS), "content": len(CONTENT)}
    assert await _count(db, Pathway) == len(PATHWAYS)
    assert await _count(db, CareerProfile) == len(CAREERS)
    assert await _count(db, ContentItem) == len(CONTENT)
    # Every career is linked to at least one pathway.
    assert await _count(db, CareerPathway) >= len(CAREERS)


@pytest.mark.asyncio
async def test_seed_includes_vocational_secondary_branch(db: Database) -> None:
    """FR-31: the GDNN / trường-trung-học-nghề branch must exist after seeding."""
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        types = {p.type for p in (await s.execute(select(Pathway))).scalars().all()}
    assert PathwayType.VOCATIONAL_SECONDARY in types
    assert PathwayType.GDNN in types


@pytest.mark.asyncio
async def test_seed_careers_are_dieu5_a(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        careers = (await s.execute(select(CareerProfile))).scalars().all()
    assert careers
    assert all(c.dieu5_code == "a" for c in careers)
    assert all(c.version >= 1 for c in careers)


@pytest.mark.asyncio
async def test_seed_content_dieu5_codes_are_c_or_d(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        items = (await s.execute(select(ContentItem))).scalars().all()
    assert {i.dieu5_code for i in items} <= {"c", "d"}
    # At least one draft exists (to prove published-only filtering later).
    assert any(i.status == ContentStatus.DRAFT for i in items)


@pytest.mark.asyncio
async def test_seed_is_idempotent(db: Database) -> None:
    async with db.session_factory() as s:
        first = await seed_careers(s)
        await s.commit()
    async with db.session_factory() as s:
        second = await seed_careers(s)  # re-run on already-seeded DB
        await s.commit()

    assert first == second
    assert await _count(db, Pathway) == len(PATHWAYS)
    assert await _count(db, CareerProfile) == len(CAREERS)
    assert await _count(db, ContentItem) == len(CONTENT)


def test_seed_tables_nonempty() -> None:
    assert PATHWAYS and CAREERS and CONTENT
    # Every career carries at least one RIASEC code and one pathway type.
    for _name, _field, riasec, _comps, _lvl, _paths, _outlook, ptypes in CAREERS:
        assert riasec and ptypes
