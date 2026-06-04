"""Labor Market Intelligence seed (FR-34; ADR-015).

**INTENTIONALLY EMPTY.** The MVP seed creates ZERO snapshot rows.

ADR-015 is explicit: the snapshot table starts as an empty framework. Data is
only inserted when an authoritative, verifiable source is available (HTTT TTLĐ
quốc gia — Luật 74/2025 Đ.19, or an official sector report). Using fabricated or
unverified figures is explicitly prohibited (ADR-015 §Context).

The adapter for the national labor market information system is a Phase-2
concern; until then, the UI shows "chưa có dữ liệu TTLĐ" (FR-35) which is the
correct honest state rather than misleading placeholder data.

CLI: ``python -m app.labor_market.seed``
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def seed_labor_market(session: AsyncSession) -> int:  # noqa: ARG001
    """Seed function — inserts zero rows by design (ADR-015).

    Returns 0 to signal the empty framework is in place. The ``session``
    parameter is accepted for API compatibility with other seed functions but
    is intentionally unused; no rows are written.
    """
    # ADR-015: No fabricated LMI data. Adapter will populate this table later.
    return 0


async def _run() -> None:  # pragma: no cover - CLI entry point
    """CLI: ``python -m app.labor_market.seed`` — no-op, confirms empty framework."""
    from app.core.config import get_settings
    from app.core.database import Database

    db = Database(get_settings())
    try:
        async with db.session_factory() as session:
            count = await seed_labor_market(session)
            await session.commit()
        print(f"[seed] labor_market_snapshot: {count} rows (empty framework by ADR-015)")
    finally:
        await db.dispose()


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    import asyncio

    asyncio.run(_run())
