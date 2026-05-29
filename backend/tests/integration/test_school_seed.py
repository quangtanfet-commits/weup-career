"""School seed is idempotent (re-running does not duplicate the demo school)."""

from __future__ import annotations

import pytest
from app.core.database import Database
from app.school.models import School, SchoolClass
from app.school.seed import DEMO_SCHOOL_NAME, seed_schools
from sqlalchemy import func, select

pytestmark = pytest.mark.asyncio


async def test_seed_is_idempotent(db: Database) -> None:
    async with db.session_factory() as s:
        first = await seed_schools(s)
        await s.commit()
    async with db.session_factory() as s:
        second = await seed_schools(s)  # already-present branch
        await s.commit()
    assert first == second
    assert "school" in first and "class" in first

    async with db.session_factory() as s:
        schools = (await s.execute(select(func.count()).select_from(School))).scalar_one()
        classes = (
            await s.execute(
                select(func.count()).select_from(SchoolClass).where(SchoolClass.name == "9A")
            )
        ).scalar_one()
    assert schools == 1
    assert classes == 1
    # Sanity: the single school is the demo one.
    async with db.session_factory() as s:
        name = (
            await s.execute(select(School.name).where(School.id == first["school"]))
        ).scalar_one()
    assert name == DEMO_SCHOOL_NAME
