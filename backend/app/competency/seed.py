"""Seed data for the fixed competency tree (FR-20, FR-21, ADR-013).

The 12 ABCD competencies (NL1..NL12) across 3 areas (A_personal, B_exploration,
C_building), each with three NCDG-style indicators at depths K / [CRED_640AC91D] (mapping
"Nhận biết → Thực hiện-Vận dụng → Phản tư", CTGDPT 2018). Every competency
carries its TT 16/2026 Điều 5 crosswalk (``dieu5_codes``) and every indicator
its primary ``dieu5_code``.

Idempotent: a competency with the same ``code`` already present is left
untouched (and its indicators are not duplicated). Safe to re-run on every
deploy. CLI: ``python -m app.competency.seed`` (mirrors assessments/seed.py).

Content is MVP placeholder pedagogy pending the full ILO Việt Nam item bank
(sources.md §2); the structure (codes, areas, depths, Điều 5 mapping) is the
load-bearing part and is stable.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import CompetencyArea, Depth

# (code, area, name_vi, name_en, dieu5_codes) for the 12 ABCD competencies.
COMPETENCIES: list[tuple[str, CompetencyArea, str, str, list[str]]] = [
    # A — Personal management (hiểu mình)
    (
        "NL1",
        CompetencyArea.A_PERSONAL,
        "Hiểu bản thân (sở thích, giá trị, năng lực)",
        "Self-understanding",
        ["b"],
    ),
    (
        "NL2",
        CompetencyArea.A_PERSONAL,
        "Xây dựng hình ảnh và sự tự tin tích cực",
        "Positive self-concept",
        ["b"],
    ),
    (
        "NL3",
        CompetencyArea.A_PERSONAL,
        "Tương tác và làm việc với người khác",
        "Interacting with others",
        ["b"],
    ),
    (
        "NL4",
        CompetencyArea.A_PERSONAL,
        "Quản lý sức khỏe tinh thần và cảm xúc",
        "Mental health & wellbeing",
        ["b"],
    ),
    # B — Exploration (khám phá thế giới nghề)
    (
        "NL5",
        CompetencyArea.B_EXPLORATION,
        "Khám phá thông tin nghề nghiệp",
        "Exploring career information",
        ["a", "d"],
    ),
    (
        "NL6",
        CompetencyArea.B_EXPLORATION,
        "Hiểu mối liên hệ giữa học tập và nghề nghiệp",
        "Linking learning to work",
        ["a"],
    ),
    (
        "NL7",
        CompetencyArea.B_EXPLORATION,
        "Hiểu thị trường lao động và xu hướng",
        "Understanding the labour market",
        ["a"],
    ),
    (
        "NL8",
        CompetencyArea.B_EXPLORATION,
        "Tìm kiếm và đánh giá nguồn thông tin nghề",
        "Locating & evaluating career info",
        ["a"],
    ),
    # C — Building (xây dựng lộ trình)
    (
        "NL9",
        CompetencyArea.C_BUILDING,
        "Trải nghiệm và thử nghiệm nghề nghiệp",
        "Experiencing work",
        ["d"],
    ),
    (
        "NL10",
        CompetencyArea.C_BUILDING,
        "Ra quyết định nghề nghiệp",
        "Career decision-making",
        ["c"],
    ),
    (
        "NL11",
        CompetencyArea.C_BUILDING,
        "Lập kế hoạch và quản lý lộ trình nghề",
        "Career planning & management",
        ["c"],
    ),
    (
        "NL12",
        CompetencyArea.C_BUILDING,
        "Chuyển tiếp và thích ứng nghề nghiệp",
        "Career transitions & adaptability",
        ["c"],
    ),
]

# Per-depth indicator statement template, keyed by depth. Each competency gets
# one indicator per depth, phrased generically against the competency name.
_DEPTH_TEMPLATE_VI: dict[Depth, str] = {
    Depth.K: "Nhận biết các khái niệm cơ bản về: {name}.",
    Depth.A: "Thực hiện và vận dụng vào tình huống thực tế: {name}.",
    Depth.R: "Phản tư và điều chỉnh cách tiếp cận của bản thân về: {name}.",
}


async def seed_competencies(session: AsyncSession) -> dict[str, str]:
    """Idempotently create the 12 competencies + their indicators.

    Returns ``{code: competency_id}``. A competency already present (by ``code``)
    is left untouched; indicators are only created for newly inserted
    competencies. Caller commits.
    """
    from app.competency.models import Competency, Indicator
    from app.core.models import new_uuid

    ids: dict[str, str] = {}
    for code, area, name_vi, name_en, dieu5 in COMPETENCIES:
        existing = (
            (await session.execute(select(Competency).where(Competency.code == code)))
            .scalars()
            .first()
        )
        if existing is not None:
            ids[code] = existing.id
            continue
        comp = Competency(
            id=new_uuid(),
            code=code,
            area=area,
            name_vi=name_vi,
            name_en=name_en,
            dieu5_codes=",".join(dieu5),
        )
        session.add(comp)
        await session.flush()
        primary_dieu5 = dieu5[0] if dieu5 else "b"
        for depth in (Depth.K, Depth.A, Depth.R):
            session.add(
                Indicator(
                    id=new_uuid(),
                    competency_id=comp.id,
                    depth=depth,
                    statement_vi=_DEPTH_TEMPLATE_VI[depth].format(name=name_vi),
                    dieu5_code=primary_dieu5,
                    source_ref="mvp-seed",
                )
            )
        ids[code] = comp.id
    return ids


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: `python -m app.competency.seed` — seed the competency tree."""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            ids = await seed_competencies(session)
            await session.commit()
        print(f"[seed] competencies ready: {len(ids)} ({sorted(ids)})")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
