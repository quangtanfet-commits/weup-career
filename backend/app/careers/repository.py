"""Careers repositories — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.

This is **public reference content** (Điều 5(a/c/d)) — there is no per-user
ownership scoping here (unlike assessments/progress). Filtering by RIASEC,
field, training level (careers) and by dieu5/competency/dev_phase/school_level
(content) happens at the data layer where it maps cleanly to indexed columns;
RIASEC matching is a substring filter over the comma-joined ``riasec_codes``.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.careers.models import CareerProfile, ContentItem
from app.core.enums import (
    ContentStatus,
    DevPhase,
    PathwayType,
    RiasecCode,
    SchoolLevel,
    TrainingLevel,
)


class ICareerRepo(Protocol):
    async def list_careers(
        self,
        *,
        riasec: RiasecCode | None = None,
        field: str | None = None,
        training_level: TrainingLevel | None = None,
        pathway_type: PathwayType | None = None,
    ) -> list[CareerProfile]: ...
    async def get_career(self, career_id: str) -> CareerProfile | None: ...
    async def list_content(
        self,
        *,
        dieu5_code: str | None = None,
        competency_code: str | None = None,
        dev_phase: DevPhase | None = None,
        school_level: SchoolLevel | None = None,
        status: ContentStatus | None = None,
    ) -> list[ContentItem]: ...
    async def add_content(self, item: ContentItem) -> ContentItem: ...
    async def get_content(self, content_id: str) -> ContentItem | None: ...
    async def latest_published_version(self, content_id: str) -> ContentItem | None: ...


class SqlCareerRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_careers(
        self,
        *,
        riasec: RiasecCode | None = None,
        field: str | None = None,
        training_level: TrainingLevel | None = None,
        pathway_type: PathwayType | None = None,
    ) -> list[CareerProfile]:
        stmt = select(CareerProfile).order_by(CareerProfile.name)
        if riasec is not None:
            # Comma-joined letters; ",I," membership test avoids substring
            # false positives between single-letter codes.
            stmt = stmt.where(
                ("," + CareerProfile.riasec_codes + ",").contains(f",{riasec.value},")
            )
        if field is not None:
            stmt = stmt.where(CareerProfile.field == field)
        if training_level is not None:
            stmt = stmt.where(CareerProfile.training_level == training_level)
        if pathway_type is not None:
            from app.careers.models import CareerPathway, Pathway

            stmt = (
                stmt.join(CareerPathway, CareerPathway.career_id == CareerProfile.id)
                .join(Pathway, Pathway.id == CareerPathway.pathway_id)
                .where(Pathway.type == pathway_type)
                .distinct()
            )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_career(self, career_id: str) -> CareerProfile | None:
        return await self._session.get(CareerProfile, career_id)

    async def list_content(
        self,
        *,
        dieu5_code: str | None = None,
        competency_code: str | None = None,
        dev_phase: DevPhase | None = None,
        school_level: SchoolLevel | None = None,
        status: ContentStatus | None = None,
    ) -> list[ContentItem]:
        stmt = select(ContentItem).order_by(ContentItem.title)
        if dieu5_code is not None:
            stmt = stmt.where(ContentItem.dieu5_code == dieu5_code)
        if competency_code is not None:
            stmt = stmt.where(ContentItem.competency_code == competency_code)
        if dev_phase is not None:
            stmt = stmt.where(ContentItem.dev_phase == dev_phase)
        if school_level is not None:
            stmt = stmt.where(ContentItem.school_level == school_level)
        if status is not None:
            stmt = stmt.where(ContentItem.status == status)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_content(self, item: ContentItem) -> ContentItem:
        self._session.add(item)
        await self._session.flush()
        return item

    async def get_content(self, content_id: str) -> ContentItem | None:
        return await self._session.get(ContentItem, content_id)

    async def latest_published_version(self, content_id: str) -> ContentItem | None:
        """The currently-published row in ``content_id``'s lineage, if any.

        ``content_id`` may be any version row in the lineage. A row's lineage is
        ``lineage_id`` when set, else its own id (legacy/seed rows). Returns the
        single published version in that lineage (the row a new publish archives),
        or ``None`` if none is published.
        """
        anchor = await self._session.get(ContentItem, content_id)
        if anchor is None:
            return None
        lineage = anchor.lineage_id or anchor.id
        stmt = select(ContentItem).where(
            ((ContentItem.lineage_id == lineage) | (ContentItem.id == lineage)),
            ContentItem.status == ContentStatus.PUBLISHED,
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()
