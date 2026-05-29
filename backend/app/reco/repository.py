"""Recommendation repository — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.

Ownership / [CRED_4FFE96A2] (CP-4, G-6): ``get_by_id`` fetches a recommendation by id and
the *service* applies the relational ``can_access`` decision (owner / [CRED_E96EE5B5]
guardian / [CRED_3A1FB5BB] counselor) before returning it; a recommendation the actor
has no relation to surfaces as 404. The repo also exposes read access to the
seeded reference data the engine needs (``list_careers`` / ``list_pathways``)
so the service can build an engine profile without importing the careers
slice's service.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments.models import AssessmentInstrument, AssessmentResult
from app.careers.models import CareerProfile, Pathway
from app.competency.models import Competency, LearnerProgress
from app.reco.models import Recommendation


class IRecoRepo(Protocol):
    async def add(self, reco: Recommendation) -> Recommendation: ...
    async def get_by_id(self, reco_id: str) -> Recommendation | None: ...
    async def list_careers(self) -> list[CareerProfile]: ...
    async def list_pathways(self) -> list[Pathway]: ...
    async def latest_results(
        self, user_id: str
    ) -> list[tuple[AssessmentResult, AssessmentInstrument]]: ...
    async def progress_rows(self, user_id: str) -> list[tuple[LearnerProgress, Competency]]: ...


class SqlRecoRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, reco: Recommendation) -> Recommendation:
        self._session.add(reco)
        await self._session.flush()
        return reco

    async def get_by_id(self, reco_id: str) -> Recommendation | None:
        return await self._session.get(Recommendation, reco_id)

    async def list_careers(self) -> list[CareerProfile]:
        result = await self._session.execute(select(CareerProfile).order_by(CareerProfile.id))
        return list(result.scalars().all())

    async def list_pathways(self) -> list[Pathway]:
        result = await self._session.execute(select(Pathway).order_by(Pathway.id))
        return list(result.scalars().all())

    async def latest_results(
        self, user_id: str
    ) -> list[tuple[AssessmentResult, AssessmentInstrument]]:
        """The highest-version ``AssessmentResult`` per instrument for a user (CP-4).

        Scoped to ``user_id`` so no foreign result is read. Joins the instrument
        so the service knows each result's type (riasec/vips/mbti) without a
        second round-trip. Only the latest take per instrument is returned
        (FR-15 keeps every version; the engine uses the most recent).
        """
        max_version = (
            select(
                AssessmentResult.instrument_id.label("instrument_id"),
                func.max(AssessmentResult.version).label("max_version"),
            )
            .where(AssessmentResult.user_id == user_id)
            .group_by(AssessmentResult.instrument_id)
            .subquery()
        )
        stmt = (
            select(AssessmentResult, AssessmentInstrument)
            .join(
                AssessmentInstrument,
                AssessmentInstrument.id == AssessmentResult.instrument_id,
            )
            .join(
                max_version,
                (AssessmentResult.instrument_id == max_version.c.instrument_id)
                & (AssessmentResult.version == max_version.c.max_version),
            )
            .where(AssessmentResult.user_id == user_id)
            .order_by(AssessmentInstrument.type)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def progress_rows(self, user_id: str) -> list[tuple[LearnerProgress, Competency]]:
        """All progress rows for ``user_id`` joined to their competency (CP-4)."""
        stmt = (
            select(LearnerProgress, Competency)
            .join(Competency, Competency.id == LearnerProgress.competency_id)
            .where(LearnerProgress.user_id == user_id)
            .order_by(LearnerProgress.achieved_at)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]
