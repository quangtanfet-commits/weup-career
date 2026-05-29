"""Seed wellbeing content (FR-70): ABCD NL4, dieu5_code='b'.

Stress / MBTI / when-to-seek-help) content, surfaced through the existing
``GET /content`` filter (``dieu5=b`` / competency=NL4)``). Idempotent: a unit already
present (by ``title``) is left untouched. Safe to re-run on every deploy.
CLI: ``python -m app.wellbeing.seed``.

These are educational/self-awareness units only. There is NO diagnosis or risk
content here (NG-03) — recognising "when to ask for support" routes the student
to a counselor via ``POST /wellbeing/support-request``, it does not assess them.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ContentStatus, Depth, DevPhase, SchoolLevel

_SOURCE = "WeUp Wellbeing (NL4, TT 18/2025) — MVP placeholder"
_NL4 = "NL4"
_DIEU5_B = "b"

# (title, depth, dev_phase, school_level)
WELLBEING_CONTENT: list[tuple[str, Depth, DevPhase, SchoolLevel]] = [
    (
        "Quản lý căng thẳng trong học tập",
        Depth.K,
        DevPhase.EXPLORATION,
        SchoolLevel.LOWER_SECONDARY,
    ),
    (
        "Cân bằng học tập và cuộc sống",
        Depth.A,
        DevPhase.EXPLORATION,
        SchoolLevel.LOWER_SECONDARY,
    ),
    (
        "Nhận biết khi nào cần tìm sự hỗ trợ",
        Depth.K,
        DevPhase.PLANNING,
        SchoolLevel.UPPER_SECONDARY,
    ),
]


async def seed_wellbeing(session: AsyncSession) -> dict[str, int]:
    """Idempotently seed the NL4 dieu5=b wellbeing content units.

    Returns ``{"content": n}`` — the number of wellbeing units defined. Existing
    rows (by title) are left untouched. Caller commits.
    """
    from app.careers.models import ContentItem
    from app.core.models import new_uuid

    for title, depth, phase, level in WELLBEING_CONTENT:
        existing = (
            (await session.execute(select(ContentItem).where(ContentItem.title == title)))
            .scalars()
            .first()
        )
        if existing is not None:
            continue
        new_id = new_uuid()
        session.add(
            ContentItem(
                id=new_id,
                title=title,
                body=f"[MVP placeholder] {title}.",
                dieu5_code=_DIEU5_B,
                competency_code=_NL4,
                depth=depth,
                dev_phase=phase,
                school_level=level,
                version=1,
                status=ContentStatus.PUBLISHED,
                source_ref=_SOURCE,
                lineage_id=new_id,
            )
        )

    await session.flush()
    return {"content": len(WELLBEING_CONTENT)}


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: `python -m app.wellbeing.seed` — seed wellbeing content."""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            counts = await seed_wellbeing(session)
            await session.commit()
        print(f"[seed] wellbeing ready: {counts}")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
