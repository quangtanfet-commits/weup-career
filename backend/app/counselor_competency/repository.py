"""Counselor-competency repository — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): service depends on Protocol, not SQLAlchemy.

All queries are scoped to a single counselor's data; no cross-user reads exist.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.counselor_competency.models import CounselorCompetency, CounselorSelfAssessment


class ICounselorCompetencyRepo(Protocol):
    async def list_competencies(self) -> list[CounselorCompetency]: ...

    async def get_competency_by_code(self, code: str) -> CounselorCompetency | None: ...

    async def next_version(self, *, counselor_id: str) -> int: ...

    async def add_self_assessment(
        self, assessment: CounselorSelfAssessment
    ) -> CounselorSelfAssessment: ...

    async def list_self_assessments(
        self, *, counselor_id: str
    ) -> list[CounselorSelfAssessment]: ...


class SqlCounselorCompetencyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_competencies(self) -> list[CounselorCompetency]:
        """All framework entries, ordered by code."""
        result = await self._session.execute(
            select(CounselorCompetency).order_by(CounselorCompetency.code)
        )
        return list(result.scalars().all())

    async def get_competency_by_code(self, code: str) -> CounselorCompetency | None:
        result = await self._session.execute(
            select(CounselorCompetency).where(CounselorCompetency.code == code)
        )
        return result.scalars().first()

    async def next_version(self, *, counselor_id: str) -> int:
        """One more than the current maximum version for this counselor (1 if first)."""
        result = await self._session.execute(
            select(func.max(CounselorSelfAssessment.version)).where(
                CounselorSelfAssessment.counselor_id == counselor_id
            )
        )
        current_max: int | None = result.scalar()
        return 1 if current_max is None else current_max + 1

    async def add_self_assessment(
        self, assessment: CounselorSelfAssessment
    ) -> CounselorSelfAssessment:
        self._session.add(assessment)
        await self._session.flush()
        return assessment

    async def list_self_assessments(
        self, *, counselor_id: str
    ) -> list[CounselorSelfAssessment]:
        """All self-assessments for one counselor, latest version first."""
        result = await self._session.execute(
            select(CounselorSelfAssessment)
            .where(CounselorSelfAssessment.counselor_id == counselor_id)
            .order_by(CounselorSelfAssessment.version.desc())
        )
        return list(result.scalars().all())
