"""Wellbeing seed is idempotent and tags content NL4 / [TOKEN_d0c9b8a7] (FR-70)."""

from __future__ import annotations

import pytest
from app.careers.models import ContentItem
from app.core.database import Database
from app.wellbeing.seed import WELLBEING_CONTENT, seed_wellbeing
from sqlalchemy import func, select

pytestmark = pytest.mark.asyncio


async def test_seed_is_idempotent(db: Database) -> None:
    async with db.session_factory() as s:
        first = await seed_wellbeing(s)
        await s.commit()
    async with db.session_factory() as s:
        second = await seed_wellbeing(s)  # already-present branch
        await s.commit()
    assert first == second == {"content": len(WELLBEING_CONTENT)}

    async with db.session_factory() as s:
        count = (
            await s.execute(
                select(func.count())
                .select_from(ContentItem)
                .where(ContentItem.competency_code == "NL4", ContentItem.dieu5_code == "b")
            )
        ).scalar_one()
    assert count == len(WELLBEING_CONTENT)


async def test_seeded_wellbeing_is_published_and_tagged(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_wellbeing(s)
        await s.commit()
    async with db.session_factory() as s:
        rows = (
            (await s.execute(select(ContentItem).where(ContentItem.competency_code == "NL4")))
            .scalars()
            .all()
        )
    assert rows
    for row in rows:
        assert row.dieu5_code == "b"
        assert row.status.value == "published"
        assert row.version == 1
        assert row.lineage_id == row.id
