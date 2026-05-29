"""Guardian repositories — Port (Protocol) + SQLAlchemy adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssuranceLevel, ConsentStatus
from app.guardians.models import GuardianConsent, GuardianLink


class IGuardianRepo(Protocol):
    async def add_link(self, link: GuardianLink) -> GuardianLink: ...
    async def get_link(self, link_id: str) -> GuardianLink | None: ...
    async def get_link_for_child_guardian(
        self, child_user_id: str, guardian_user_id: str
    ) -> GuardianLink | None: ...
    async def add_consent(self, consent: GuardianConsent) -> GuardianConsent: ...
    async def get_active_consent(self, child_user_id: str) -> GuardianConsent | None: ...
    async def has_active_consent(self, child_user_id: str) -> bool: ...
    async def best_assurance_for_child(self, child_user_id: str) -> AssuranceLevel | None: ...
    async def revoke_consent(self, consent: GuardianConsent, *, when: datetime) -> None: ...


class SqlGuardianRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_link(self, link: GuardianLink) -> GuardianLink:
        self._session.add(link)
        await self._session.flush()
        return link

    async def get_link(self, link_id: str) -> GuardianLink | None:
        return await self._session.get(GuardianLink, link_id)

    async def get_link_for_child_guardian(
        self, child_user_id: str, guardian_user_id: str
    ) -> GuardianLink | None:
        result = await self._session.execute(
            select(GuardianLink).where(
                GuardianLink.child_user_id == child_user_id,
                GuardianLink.guardian_user_id == guardian_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def add_consent(self, consent: GuardianConsent) -> GuardianConsent:
        self._session.add(consent)
        await self._session.flush()
        return consent

    async def get_active_consent(self, child_user_id: str) -> GuardianConsent | None:
        result = await self._session.execute(
            select(GuardianConsent).where(
                GuardianConsent.child_user_id == child_user_id,
                GuardianConsent.status == ConsentStatus.ACTIVE,
            )
        )
        return result.scalars().first()

    async def has_active_consent(self, child_user_id: str) -> bool:
        return (await self.get_active_consent(child_user_id)) is not None

    async def best_assurance_for_child(self, child_user_id: str) -> AssuranceLevel | None:
        """Assurance of the guardian link backing the child's active consent.

        Returns ``None`` when there is no active consent (FF-19 gate then sees
        the absence and applies the configured minimum). Joins the active
        consent to its originating link so the assurance reflects the actual
        consent in force, not any stale/[CRED_3CD0C8A1] link.
        """
        result = await self._session.execute(
            select(GuardianLink.assurance_level)
            .join(GuardianConsent, GuardianConsent.guardian_link_id == GuardianLink.id)
            .where(
                GuardianConsent.child_user_id == child_user_id,
                GuardianConsent.status == ConsentStatus.ACTIVE,
            )
        )
        row = result.scalars().first()
        return row if row is not None else None

    async def revoke_consent(self, consent: GuardianConsent, *, when: datetime) -> None:
        consent.status = ConsentStatus.REVOKED
        consent.revoked_at = when
        await self._session.flush()
