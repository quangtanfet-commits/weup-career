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
