"""Repository-level tests for SqlAssessmentRepo (Port adapter coverage)."""

from __future__ import annotations

import pytest
from app.assessments.models import AssessmentInstrument, AssessmentItem
from app.assessments.repository import SqlAssessmentRepo
from app.assessments.seed import INSTRUMENT_VERSION, RIASEC_ITEMS
from app.core.enums import InstrumentType
from app.core.models import new_uuid
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


async def test_list_items_returns_seeded_items(session: AsyncSession) -> None:
    repo = SqlAssessmentRepo(session)
    inst = AssessmentInstrument(
        id=new_uuid(), type=InstrumentType.RIASEC, version=INSTRUMENT_VERSION, is_active=True
    )
    session.add(inst)
    await session.flush()
    for key, prompt in RIASEC_ITEMS.items():
        session.add(
            AssessmentItem(
                id=new_uuid(),
                instrument_id=inst.id,
                item_key=key,
                competency_code="NL1",
                dieu5_code="b",
                prompt_vi=prompt,
            )
        )
    await session.flush()

    items = await repo.list_items(inst.id)
    assert len(items) == len(RIASEC_ITEMS)
    assert {i.item_key for i in items} == set(RIASEC_ITEMS)
    # Sorted by item_key (deterministic ordering).
    assert [i.item_key for i in items] == sorted(RIASEC_ITEMS)


async def test_next_version_starts_at_one(session: AsyncSession) -> None:
    repo = SqlAssessmentRepo(session)
    v = await repo.next_version(user_id="u-1", instrument_id="i-1")
    assert v == 1
