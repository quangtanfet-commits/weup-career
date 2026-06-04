"""Idempotency test for the counselor-competency framework seeder.

Gate 1 of the FR-103 assurance pass (docs/assurance/counselor-competency-fr103.md):
re-running the seeder must take the ``existing is not None`` branch
(seed.py:116-117) — identical ids returned, zero duplicate rows.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.counselor_competency.models import CounselorCompetency
from app.counselor_competency.seed import FRAMEWORK, seed_counselor_competencies


async def test_seed_is_idempotent(session: AsyncSession) -> None:
    """Second seed run reuses existing rows: same ids, no duplicates."""
    first = await seed_counselor_competencies(session)
    second = await seed_counselor_competencies(session)

    # Re-seed branch returns the existing rows' ids verbatim.
    assert second == first
    assert set(first) == {entry["code"] for entry in FRAMEWORK}

    # No duplicate rows: exactly one row per framework entry after two runs.
    total = await session.scalar(select(func.count()).select_from(CounselorCompetency))
    assert total == len(FRAMEWORK)
