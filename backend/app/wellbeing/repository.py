"""Wellbeing repository — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.
Persists the ``SupportRequest`` referral record (FR-71). No query here returns
or derives any clinical/risk signal — there is none stored (NG-03).
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.wellbeing.models import SupportRequest


class IWellbeingRepo(Protocol):
    async def add_request(self, request: SupportRequest) -> SupportRequest: ...
    async def list_for_student(self, *, student_id: str) -> list[SupportRequest]: ...


class SqlWellbeingRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_request(self, request: SupportRequest) -> SupportRequest:
        self._session.add(request)
        await self._session.flush()
        return request

    async def list_for_student(self, *, student_id: str) -> list[SupportRequest]:
        """A student's own support requests, scoped to ``student_id`` (CP-4)."""
        stmt = (
            select(SupportRequest)
            .where(SupportRequest.student_id == student_id)
            .order_by(SupportRequest.created_at)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
