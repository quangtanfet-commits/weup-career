"""Unit tests for CareerService content versioning internals (slice 7, FR-90).

Covers the defence-in-depth / [TOKEN_9c1e3f5a7b9d] paths not reachable through the HTTP
schema layer: the service-level mandatory-tag guard, the no-audit-repo branch,
and the unknown-lineage-anchor branch of ``latest_published_version``.
"""

from __future__ import annotations

import pytest
from app.careers.repository import SqlCareerRepo
from app.careers.service import CareerService, ContentDraft
from app.core.database import Database
from app.core.enums import ContentStatus, Depth, DevPhase, SchoolLevel
from app.core.exceptions import ValidationError

pytestmark = pytest.mark.asyncio


def _draft(**over: object) -> ContentDraft:
    base: dict[str, object] = {
        "title": "t",
        "body": "b",
        "competency_code": "NL1",
        "dieu5_code": "c",
        "depth": Depth.K,
        "dev_phase": DevPhase.EXPLORATION,
        "school_level": SchoolLevel.LOWER_SECONDARY,
    }
    base.update(over)
    return ContentDraft(**base)  # type: ignore[arg-type]


async def test_create_content_empty_tag_raises_validation(db: Database) -> None:
    """Service-level guard fires even if a falsy tag slips past the schema."""
    async with db.session_factory() as s:
        svc = CareerService(careers=SqlCareerRepo(s))  # no audit repo
        with pytest.raises(ValidationError) as exc:
            await svc.create_content(editor_id="e1", draft=_draft(competency_code=""))
        assert "missing_tags" in exc.value.details


async def test_create_content_without_audit_repo(db: Database) -> None:
    """``audit=None`` is a valid wiring — create still succeeds, no audit write."""
    async with db.session_factory() as s:
        svc = CareerService(careers=SqlCareerRepo(s))
        item = await svc.create_content(editor_id="e1", draft=_draft())
        await s.commit()
    assert item.version == 1
    assert item.status is ContentStatus.DRAFT
    assert item.lineage_id == item.id


async def test_latest_published_version_unknown_anchor_is_none(db: Database) -> None:
    """An unknown content id yields no published-version anchor (None)."""
    async with db.session_factory() as s:
        repo = SqlCareerRepo(s)
        assert await repo.latest_published_version("no-such-id") is None
