"""Assessment repositories — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.
Ownership is always enforced by filtering on ``user_id`` at the data layer
(auth-design §"Thực thi quyền sở hữu") — a foreign result is simply not found.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments.models import (
    AssessmentInstrument,
    AssessmentItem,
    AssessmentResult,
)
from app.core.enums import InstrumentType


class IAssessmentRepo(Protocol):
    async def list_active_instruments(self) -> list[AssessmentInstrument]: ...
    async def get_active_instrument(
        self, instrument_type: InstrumentType
    ) -> AssessmentInstrument | None: ...
    async def list_items(self, instrument_id: str) -> list[AssessmentItem]: ...
    async def add_result(self, result: AssessmentResult) -> AssessmentResult: ...
    async def next_version(self, *, user_id: str, instrument_id: str) -> int: ...
    async def get_owned_result(
        self, *, result_id: str, user_id: str
    ) -> AssessmentResult | None: ...
    async def delete_result(self, result: AssessmentResult) -> None: ...


class SqlAssessmentRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active_instruments(self) -> list[AssessmentInstrument]:
        result = await self._session.execute(
            select(AssessmentInstrument)
            .where(AssessmentInstrument.is_active.is_(True))
            .order_by(AssessmentInstrument.type)
        )
        return list(result.scalars().all())

    async def get_active_instrument(
        self, instrument_type: InstrumentType
    ) -> AssessmentInstrument | None:
        result = await self._session.execute(
            select(AssessmentInstrument).where(
                AssessmentInstrument.type == instrument_type,
                AssessmentInstrument.is_active.is_(True),
            )
        )
        return result.scalars().first()

    async def list_items(self, instrument_id: str) -> list[AssessmentItem]:
        result = await self._session.execute(
            select(AssessmentItem)
            .where(AssessmentItem.instrument_id == instrument_id)
            .order_by(AssessmentItem.item_key)
        )
        return list(result.scalars().all())

    async def add_result(self, result: AssessmentResult) -> AssessmentResult:
        self._session.add(result)
        await self._session.flush()
        return result

    async def next_version(self, *, user_id: str, instrument_id: str) -> int:
        """Next version number for (user, instrument): retake → version+1 (FR-15)."""
        result = await self._session.execute(
            select(func.max(AssessmentResult.version)).where(
                AssessmentResult.user_id == user_id,
                AssessmentResult.instrument_id == instrument_id,
            )
        )
        current = result.scalar_one_or_none()
        return int(current) + 1 if current is not None else 1

    async def get_owned_result(
        self, *, result_id: str, user_id: str
    ) -> AssessmentResult | None:
        """Fetch a result only if owned by ``user_id`` (CP-4 — no cross-user read)."""
        result = await self._session.execute(
            select(AssessmentResult).where(
                AssessmentResult.id == result_id,
                AssessmentResult.user_id == user_id,
            )
        )
        return result.scalars().first()

    async def delete_result(self, result: AssessmentResult) -> None:
        await self._session.delete(result)
        await self._session.flush()
