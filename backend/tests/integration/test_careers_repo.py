"""Careers repository + service unit-ish tests against in-memory SQLite.

Covers filter branches not reachable through the router defaults — notably
``list_content(status=None)`` (return drafts + published together) and the
service's published-only default.
"""

from __future__ import annotations

import pytest
from app.careers.repository import SqlCareerRepo
from app.careers.seed import seed_careers
from app.careers.service import CareerService
from app.core.database import Database
from app.core.enums import ContentStatus, PathwayType, RiasecCode, TrainingLevel
from app.core.exceptions import NotFoundError

pytestmark = pytest.mark.asyncio


async def test_list_content_status_none_returns_all(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        repo = SqlCareerRepo(s)
        all_items = await repo.list_content(status=None)
        published = await repo.list_content(status=ContentStatus.PUBLISHED)
        drafts = await repo.list_content(status=ContentStatus.DRAFT)
    # status=None must include both published and draft rows.
    assert len(all_items) == len(published) + len(drafts)
    assert drafts and published


async def test_service_default_is_published_only(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        service = CareerService(careers=SqlCareerRepo(s))
        items = await service.list_content()  # default status filter
    assert items and all(i.status == ContentStatus.PUBLISHED for i in items)


async def test_repo_riasec_membership_no_false_positive(db: Database) -> None:
    """RIASEC filter uses delimited membership, not raw substring."""
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        repo = SqlCareerRepo(s)
        investigative = await repo.list_careers(riasec=RiasecCode.I)
    assert investigative
    assert all("I" in r.riasec_codes.split(",") for r in investigative)


async def test_repo_pathway_filter(db: Database) -> None:
    async with db.session_factory() as s:
        await seed_careers(s)
        await s.commit()
        repo = SqlCareerRepo(s)
        voc = await repo.list_careers(pathway_type=PathwayType.VOCATIONAL_SECONDARY)
        uni = await repo.list_careers(training_level=TrainingLevel.UNIVERSITY)
    assert voc and uni


async def test_service_get_career_unknown_raises(db: Database) -> None:
    async with db.session_factory() as s:
        service = CareerService(careers=SqlCareerRepo(s))
        with pytest.raises(NotFoundError):
            await service.get_career("nope")
