"""Audit writer (CP-3 ready). Append-only; same-transaction with the action.

For sensitive reads, the caller MUST write the audit record in the SAME
transaction as the read so there is no read path that skips audit (ADR-011).
This slice has no sensitive data yet, but auth/consent events are audited.
"""

from __future__ import annotations

from typing import Protocol

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit_models import AuditLog
from app.core.logging import correlation_id_var


class IAuditRepo(Protocol):
    async def record(
        self,
        *,
        action: str,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        is_sensitive_access: bool = False,
    ) -> AuditLog: ...

    async def count(self) -> int: ...
    async def count_sensitive(self) -> int: ...


class SqlAuditRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(
        self,
        *,
        action: str,
        actor_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        is_sensitive_access: bool = False,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            is_sensitive_access=is_sensitive_access,
            correlation_id=correlation_id_var.get(),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def count(self) -> int:
        result = await self._session.execute(select(func.count()).select_from(AuditLog))
        return int(result.scalar_one())

    async def count_sensitive(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.is_sensitive_access.is_(True))
        )
        return int(result.scalar_one())
