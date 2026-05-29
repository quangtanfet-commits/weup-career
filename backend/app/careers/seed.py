"""Seed data for the public career library + 5c/5d content (FR-30..33/40..42/50..51).

MVP placeholder occupations, phân luồng pathways, and learning-content units so
the careers/content flow is exercisable end-to-end. Content is **versioned**
(FR-33, NFR-26): swapping in the real ILO Việt Nam "Sách tra cứu nghề"
(sources.md §2.7) is a new version, not a code change.

The seed deliberately includes the **GDNN / "trường trung học nghề"** pathway
(Luật GDNN 124/2025, FR-31) and at least one career reachable through it, so the
vocational-secondary branch is queryable from day one.

Idempotent: rows already present (by their natural key — pathway ``type``,
career ``name``, content ``title``) are left untouched and links are not
duplicated. Safe to re-run on every deploy. CLI: ``python -m app.careers.seed``
(mirrors competency/seed.py).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    ContentStatus,
    Depth,
    DevPhase,
    PathwayType,
    SchoolLevel,
    TrainingLevel,
)

_SOURCE = "ILO VN — Sách tra cứu nghề 2020 (sources.md §2.7) — MVP placeholder"

# (type, name, description) for the phân luồng pathways.
PATHWAYS: list[tuple[PathwayType, str, str]] = [
    (PathwayType.ACADEMIC, "Học tiếp THPT → Đại học", "Lộ trình học thuật sau THCS."),
    (
        PathwayType.VOCATIONAL_SECONDARY,
        "Trường trung học nghề",
        "Nhánh trung học nghề sau THCS (Luật GDNN 124/2025).",
    ),
    (
        PathwayType.GDNN,
        "Giáo dục nghề nghiệp (TC/CĐ nghề)",
        "Hệ thống GDNN: trung cấp, cao đẳng nghề.",
    ),
    (PathwayType.LABOR, "Tham gia thị trường lao động", "Học nghề ngắn hạn và đi làm sớm."),
]

# (name, field, riasec, required_competencies, training_level, training_paths,
#  outlook, pathway_types) for the MVP careers.
CAREERS: list[tuple[str, str, list[str], list[str], TrainingLevel, str, str, list[PathwayType]]] = [
    (
        "Kỹ sư phần mềm",
        "technology",
        ["I", "R"],
        ["NL5", "NL6"],
        TrainingLevel.UNIVERSITY,
        "Cử nhân/kỹ sư CNTT; cũng có thể qua cao đẳng nghề + tự học.",
        "Nhu cầu cao, tăng trưởng ổn định.",
        [PathwayType.ACADEMIC, PathwayType.GDNN],
    ),
    (
        "Điều dưỡng viên",
        "health",
        ["S", "I"],
        ["NL3", "NL4"],
        TrainingLevel.COLLEGE,
        "Cao đẳng/đại học điều dưỡng.",
        "Nhu cầu ổn định, đặc biệt ở bệnh viện và chăm sóc người cao tuổi.",
        [PathwayType.ACADEMIC, PathwayType.GDNN],
    ),
    (
        "Kỹ thuật viên cơ khí",
        "engineering",
        ["R", "C"],
        ["NL5", "NL9"],
        TrainingLevel.VOCATIONAL,
        "Trường trung học nghề hoặc trung cấp/cao đẳng nghề cơ khí.",
        "Nhu cầu vững ở sản xuất, bảo trì, lắp ráp.",
        [PathwayType.VOCATIONAL_SECONDARY, PathwayType.GDNN, PathwayType.LABOR],
    ),
    (
        "Nhà thiết kế đồ họa",
        "creative",
        ["A", "E"],
        ["NL1", "NL10"],
        TrainingLevel.COLLEGE,
        "Cao đẳng/đại học mỹ thuật ứng dụng; nhiều người tự học qua dự án.",
        "Nhu cầu tăng theo kinh tế số và truyền thông.",
        [PathwayType.ACADEMIC, PathwayType.GDNN],
    ),
]

# (title, dieu5_code, competency_code, depth, dev_phase, school_level, status)
# for the 5c (kỹ năng chọn nghề) and 5d (trải nghiệm nghề) content.
CONTENT: list[
    tuple[str, str, str, Depth | None, DevPhase | None, SchoolLevel | None, ContentStatus]
] = [
    (
        "Quy trình ra quyết định nghề nghiệp",
        "c",
        "NL10",
        Depth.A,
        DevPhase.PLANNING,
        SchoolLevel.UPPER_SECONDARY,
        ContentStatus.PUBLISHED,
    ),
    (
        "So sánh ngành/nghề theo tiêu chí cá nhân",
        "c",
        "NL12",
        Depth.A,
        DevPhase.PLANNING,
        SchoolLevel.UPPER_SECONDARY,
        ContentStatus.PUBLISHED,
    ),
    (
        "Một ngày làm nghề: Kỹ sư phần mềm",
        "d",
        "NL5",
        Depth.K,
        DevPhase.EXPLORATION,
        SchoolLevel.LOWER_SECONDARY,
        ContentStatus.PUBLISHED,
    ),
    (
        "Nhật ký trải nghiệm nghề (mẫu logbook)",
        "d",
        "NL9",
        Depth.A,
        DevPhase.EXPLORATION,
        SchoolLevel.LOWER_SECONDARY,
        ContentStatus.PUBLISHED,
    ),
    # An unpublished draft — should NOT appear in default public listings.
    (
        "Trải nghiệm nghề nâng cao (bản nháp)",
        "d",
        "NL9",
        Depth.R,
        DevPhase.PLANNING,
        SchoolLevel.UPPER_SECONDARY,
        ContentStatus.DRAFT,
    ),
]


async def seed_careers(session: AsyncSession) -> dict[str, int]:
    """Idempotently seed pathways, careers (+ links), and content.

    Returns counts ``{"pathways": n, "careers": n, "content": n}`` of rows that
    exist after seeding. Existing rows (by natural key) are left untouched and
    career↔pathway links are not duplicated. Caller commits.
    """
    from app.careers.models import CareerPathway, CareerProfile, ContentItem, Pathway
    from app.core.models import new_uuid

    # -- pathways -------------------------------------------------------
    pathway_ids: dict[PathwayType, str] = {}
    for ptype, name, desc in PATHWAYS:
        existing_p = (
            (await session.execute(select(Pathway).where(Pathway.type == ptype))).scalars().first()
        )
        if existing_p is not None:
            pathway_ids[ptype] = existing_p.id
            continue
        pid = new_uuid()
        session.add(Pathway(id=pid, name=name, type=ptype, description=desc))
        pathway_ids[ptype] = pid
    await session.flush()

    # -- careers + links ------------------------------------------------
    # Insert the career rows first and flush so their PKs exist before the
    # career_pathway FK rows reference them (SQLite enforces FKs immediately).
    new_links: list[tuple[str, list[PathwayType]]] = []
    for name, field, riasec, comps, level, paths, outlook, ptypes in CAREERS:
        existing_c = (
            (await session.execute(select(CareerProfile).where(CareerProfile.name == name)))
            .scalars()
            .first()
        )
        if existing_c is not None:
            continue
        cid = new_uuid()
        session.add(
            CareerProfile(
                id=cid,
                name=name,
                field=field,
                riasec_codes=",".join(riasec),
                required_competencies=",".join(comps),
                training_level=level,
                training_paths=paths,
                labor_market_outlook=outlook,
                source_ref=_SOURCE,
                version=1,
                dieu5_code="a",
            )
        )
        new_links.append((cid, ptypes))
    await session.flush()
    for cid, ptypes in new_links:
        for ptype in ptypes:
            session.add(CareerPathway(id=new_uuid(), career_id=cid, pathway_id=pathway_ids[ptype]))

    # -- content --------------------------------------------------------
    for title, dieu5, comp, depth, phase, level_c, status in CONTENT:
        existing_ci = (
            (await session.execute(select(ContentItem).where(ContentItem.title == title)))
            .scalars()
            .first()
        )
        if existing_ci is not None:
            continue
        session.add(
            ContentItem(
                id=new_uuid(),
                title=title,
                body=f"[MVP placeholder] {title}.",
                dieu5_code=dieu5,
                competency_code=comp,
                depth=depth,
                dev_phase=phase,
                school_level=level_c,
                version=1,
                status=status,
                source_ref=_SOURCE,
            )
        )

    await session.flush()
    return {
        "pathways": len(PATHWAYS),
        "careers": len(CAREERS),
        "content": len(CONTENT),
    }


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: `python -m app.careers.seed` — seed the public career library."""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            counts = await seed_careers(session)
            await session.commit()
        print(f"[seed] careers ready: {counts}")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
