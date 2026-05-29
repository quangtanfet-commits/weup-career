"""Competency repositories — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.
Learner-scoped reads (progress, domain phase) always filter on ``user_id`` at
the data layer (CP-4 ownership) — another learner's rows are simply not
returned. ``LearnerProgress`` is treated as append-only: the adapter exposes
``add_progress`` but no update/delete (CP-8).
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.competency.models import (
    Competency,
    Indicator,
    LearnerDomainPhase,
    LearnerProgress,
)


class ICompetencyRepo(Protocol):
    async def list_competencies(self) -> list[Competency]: ...
    async def list_indicators(self) -> list[Indicator]: ...
    async def get_indicator(self, indicator_id: str) -> Indicator | None: ...
    async def list_progress(self, user_id: str) -> list[LearnerProgress]: ...
    async def add_progress(self, progress: LearnerProgress) -> LearnerProgress: ...
    async def list_domain_phases(self, user_id: str) -> list[LearnerDomainPhase]: ...
    async def add_domain_phase(self, phase: LearnerDomainPhase) -> LearnerDomainPhase: ...


class SqlCompetencyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_competencies(self) -> list[Competency]:
        result = await self._session.execute(
            select(Competency).order_by(Competency.area, Competency.code)
        )
        return list(result.scalars().all())

    async def list_indicators(self) -> list[Indicator]:
        result = await self._session.execute(
            select(Indicator).order_by(Indicator.competency_id, Indicator.depth)
        )
        return list(result.scalars().all())

    async def get_indicator(self, indicator_id: str) -> Indicator | None:
        return await self._session.get(Indicator, indicator_id)

    async def list_progress(self, user_id: str) -> list[LearnerProgress]:
        """All progress rows for ``user_id`` (CP-4: scoped by owner)."""
        result = await self._session.execute(
            select(LearnerProgress)
            .where(LearnerProgress.user_id == user_id)
            .order_by(LearnerProgress.achieved_at)
        )
        return list(result.scalars().all())

    async def add_progress(self, progress: LearnerProgress) -> LearnerProgress:
        """Insert a progress row. Append-only — never updates an existing row (CP-8)."""
        self._session.add(progress)
        await self._session.flush()
        return progress

    async def list_domain_phases(self, user_id: str) -> list[LearnerDomainPhase]:
        result = await self._session.execute(
            select(LearnerDomainPhase)
            .where(LearnerDomainPhase.user_id == user_id)
            .order_by(LearnerDomainPhase.area, LearnerDomainPhase.set_at)
        )
        return list(result.scalars().all())

    async def add_domain_phase(self, phase: LearnerDomainPhase) -> LearnerDomainPhase:
        self._session.add(phase)
        await self._session.flush()
        return phase
