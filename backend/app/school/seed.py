"""Seed a demo school + class for the B2B2C channel (FR-80).

Idempotent: a school with the same ``name`` already present is left untouched
(and its class is not duplicated). Memberships (counselor/student enrollment)
are created at runtime by the school-admin flow, not seeded here — this only
ensures the demo school structure exists. CLI: ``python -m app.school.seed``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

DEMO_SCHOOL_NAME = "Trường THCS Demo WeUp"
DEMO_CLASS_NAME = "9A"


async def seed_schools(session: AsyncSession) -> dict[str, str]:
    """Idempotently create one demo school + class. Returns {school|class: id}.

    Caller commits.
    """
    from app.core.models import new_uuid
    from app.school.models import School, SchoolClass
    from app.school.repository import SqlSchoolRepo

    repo = SqlSchoolRepo(session)
    ids: dict[str, str] = {}
    existing = (
        (await session.execute(select(School).where(School.name == DEMO_SCHOOL_NAME)))
        .scalars()
        .first()
    )
    if existing is not None:
        # The demo school and its class are always seeded together, so when the
        # school is present its class is too (one_or_none would only differ in a
        # hand-corrupted DB, which is out of scope for an idempotent seeder).
        klass = (
            (
                await session.execute(
                    select(SchoolClass).where(
                        SchoolClass.school_id == existing.id,
                        SchoolClass.name == DEMO_CLASS_NAME,
                    )
                )
            )
            .scalars()
            .one()
        )
        return {"school": existing.id, "class": klass.id}

    school = await repo.add_school(
        School(id=new_uuid(), name=DEMO_SCHOOL_NAME, type="lower_secondary", region="Hà Nội")
    )
    klass = await repo.add_class(
        SchoolClass(id=new_uuid(), school_id=school.id, name=DEMO_CLASS_NAME, grade="9")
    )
    ids["school"] = school.id
    ids["class"] = klass.id
    return ids


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: `python -m app.school.seed` — seed the demo school."""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            ids = await seed_schools(session)
            await session.commit()
        print(f"[seed] school ready: {sorted(ids)}")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
