"""Account repository — Port (Protocol) + SQLAlchemy adapter.

Hexagonal (ADR-009): the service depends on the Protocol, not on SQLAlchemy.

Two responsibilities:
- **Export reads** (FR-92): gather everything the data subject owns. Every read
  is scoped to ``user_id`` (CP-4) — no foreign data is ever returned.
- **Hard purge** (FR-91/92): find soft-deleted accounts past their recovery
  window and hard-delete the user plus all owned rows. Owned data is deleted
  EXPLICITLY (not relying on DB cascade) so the purge is portable across
  SQLite/Postgres and verifiable in tests regardless of the FK-pragma state.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.assessments.models import AssessmentResult
from app.auth.models import RefreshToken, User
from app.competency.models import LearnerDomainPhase, LearnerProgress
from app.guardians.models import GuardianConsent, GuardianLink
from app.reco.models import Recommendation
from app.school.models import CounselingSession, SchoolMembership
from app.wellbeing.models import SupportRequest


class IAccountRepo(Protocol):
    # -- export reads (CP-4: all scoped to user_id) -----------------------
    async def list_results(self, user_id: str) -> list[AssessmentResult]: ...
    async def list_progress(self, user_id: str) -> list[LearnerProgress]: ...
    async def list_domain_phases(self, user_id: str) -> list[LearnerDomainPhase]: ...
    async def list_recommendations(self, user_id: str) -> list[Recommendation]: ...

    # -- purge ------------------------------------------------------------
    async def list_expired_deleted(self, *, cutoff: datetime) -> list[User]: ...
    async def hard_delete_user(self, user: User) -> None: ...


class SqlAccountRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # -- export reads -----------------------------------------------------

    async def list_results(self, user_id: str) -> list[AssessmentResult]:
        result = await self._session.execute(
            select(AssessmentResult)
            .where(AssessmentResult.user_id == user_id)
            .order_by(AssessmentResult.created_at, AssessmentResult.version)
        )
        return list(result.scalars().all())

    async def list_progress(self, user_id: str) -> list[LearnerProgress]:
        result = await self._session.execute(
            select(LearnerProgress)
            .where(LearnerProgress.user_id == user_id)
            .order_by(LearnerProgress.achieved_at)
        )
        return list(result.scalars().all())

    async def list_domain_phases(self, user_id: str) -> list[LearnerDomainPhase]:
        result = await self._session.execute(
            select(LearnerDomainPhase)
            .where(LearnerDomainPhase.user_id == user_id)
            .order_by(LearnerDomainPhase.area, LearnerDomainPhase.set_at)
        )
        return list(result.scalars().all())

    async def list_recommendations(self, user_id: str) -> list[Recommendation]:
        result = await self._session.execute(
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at)
        )
        return list(result.scalars().all())

    # -- purge ------------------------------------------------------------

    async def list_expired_deleted(self, *, cutoff: datetime) -> list[User]:
        """Soft-deleted users whose ``deleted_at`` is at/before ``cutoff``.

        ``cutoff = now - recovery_window``: a row is expired iff it was deleted
        on or before the cutoff. Rows still inside the window are excluded.
        """
        result = await self._session.execute(
            select(User).where(
                User.is_deleted.is_(True),
                User.deleted_at.is_not(None),
                User.deleted_at <= cutoff,
            )
        )
        return list(result.scalars().all())

    async def hard_delete_user(self, user: User) -> None:
        """Hard-delete a user and ALL owned rows (FR-91/92).

        Explicit per-table deletes (not DB cascade) so the purge behaves
        identically on SQLite (tests) and Postgres (prod). Rows that merely
        reference the user as a nullable FK (``recommendation.confirmed_by``,
        ``support_request.counselor_id`` when the user counselled others,
        ``counseling_session.counselor_id``) are NOT owned by the subject, so
        we only null/handle the subject's OWN data here.
        """
        uid = user.id
        # Owned data, deleted before the user row.
        await self._session.execute(delete(AssessmentResult).where(AssessmentResult.user_id == uid))
        await self._session.execute(delete(LearnerProgress).where(LearnerProgress.user_id == uid))
        await self._session.execute(
            delete(LearnerDomainPhase).where(LearnerDomainPhase.user_id == uid)
        )
        await self._session.execute(delete(Recommendation).where(Recommendation.user_id == uid))
        await self._session.execute(delete(RefreshToken).where(RefreshToken.user_id == uid))
        await self._session.execute(delete(SchoolMembership).where(SchoolMembership.user_id == uid))
        # Support requests the subject RAISED (as student).
        await self._session.execute(delete(SupportRequest).where(SupportRequest.student_id == uid))
        # Counselling sessions where the subject is the student (their record).
        await self._session.execute(
            delete(CounselingSession).where(CounselingSession.student_id == uid)
        )
        # Guardian links/consents the subject is a party to (as child OR guardian)
        # plus the consents anchored on those links.
        link_ids = (
            (
                await self._session.execute(
                    select(GuardianLink.id).where(
                        (GuardianLink.child_user_id == uid) | (GuardianLink.guardian_user_id == uid)
                    )
                )
            )
            .scalars()
            .all()
        )
        if link_ids:
            await self._session.execute(
                delete(GuardianConsent).where(GuardianConsent.guardian_link_id.in_(link_ids))
            )
        await self._session.execute(
            delete(GuardianConsent).where(GuardianConsent.child_user_id == uid)
        )
        await self._session.execute(
            delete(GuardianLink).where(
                (GuardianLink.child_user_id == uid) | (GuardianLink.guardian_user_id == uid)
            )
        )
        # Finally the user row itself.
        await self._session.delete(user)
        await self._session.flush()
