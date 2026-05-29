"""Guardian-service edge branches not reachable through the HTTP API:
child-not-found, unverified-link consent, and self-link at grant time."""

from __future__ import annotations

from datetime import datetime

import pytest
from app.auth.models import User
from app.auth.repository import SqlUserRepo
from app.core.audit import SqlAuditRepo
from app.core.enums import (
    AccountStatus,
    AgeBand,
    AssuranceLevel,
    UserType,
    VerificationMethod,
)
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    SelfConsentError,
)
from app.core.models import new_uuid
from app.guardians.models import GuardianLink
from app.guardians.repository import SqlGuardianRepo
from app.guardians.schemas import InviteRequest
from app.guardians.service import GuardianService
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.asyncio


def _service(session: AsyncSession) -> GuardianService:
    return GuardianService(
        users=SqlUserRepo(session),
        guardians=SqlGuardianRepo(session),
        audit=SqlAuditRepo(session),
    )


async def _user(session: AsyncSession, email: str, band: AgeBand) -> User:
    user = User(
        id=new_uuid(),
        email=email,
        hashed_password="x",
        date_of_birth=datetime(2010, 1, 1).date(),
        age_band=band,
        user_type=UserType.STUDENT,
        account_status=AccountStatus.PENDING_GUARDIAN_CONSENT,
    )
    session.add(user)
    await session.flush()
    return user


async def test_invite_child_not_found(session: AsyncSession) -> None:
    svc = _service(session)
    with pytest.raises(NotFoundError):
        await svc.invite(
            child_user_id="ghost-child",
            payload=InviteRequest(guardian_email="g@example.com", relationship="m"),
        )


async def test_grant_consent_unverified_link_denied(session: AsyncSession) -> None:
    """An unverified GuardianLink cannot ground a consent (assurance gate)."""
    svc = _service(session)
    child = await _user(session, "c@example.com", AgeBand.UNDER_16)
    guardian = await _user(session, "g@example.com", AgeBand.ADULT)
    link = GuardianLink(
        id=new_uuid(),
        child_user_id=child.id,
        guardian_user_id=guardian.id,
        relationship="mother",
        verification_method=VerificationMethod.EMAIL,
        assurance_level=AssuranceLevel.LOW,
        verified_at=None,  # NOT verified
    )
    session.add(link)
    await session.flush()
    with pytest.raises(PermissionDeniedError):
        await svc.grant_consent(guardian_user_id=guardian.id, guardian_link_id=link.id)


async def test_grant_then_revoke_when_child_row_missing(session: AsyncSession) -> None:
    """Defensive `if child is not None` branches: link/[CRED_2C24711E] exist but the
    child user row is absent (e.g. concurrently hard-deleted)."""
    from sqlalchemy import delete

    svc = _service(session)
    child = await _user(session, "vanish@example.com", AgeBand.UNDER_16)
    guardian = await _user(session, "gv@example.com", AgeBand.ADULT)
    link = GuardianLink(
        id=new_uuid(),
        child_user_id=child.id,
        guardian_user_id=guardian.id,
        relationship="mother",
        verification_method=VerificationMethod.EMAIL,
        assurance_level=AssuranceLevel.LOW,
        verified_at=datetime(2026, 1, 1),
    )
    session.add(link)
    await session.flush()

    # Remove the child row but keep the link.
    await session.execute(delete(User).where(User.id == child.id))
    await session.flush()

    consent = await svc.grant_consent(guardian_user_id=guardian.id, guardian_link_id=link.id)
    assert consent.status.value == "active"
    # Revoke also tolerates the missing child row.
    await svc.revoke_consent(guardian_user_id=guardian.id, child_user_id=child.id)


async def test_grant_consent_self_link_forbidden(session: AsyncSession) -> None:
    """A (corrupt) self-link is rejected at grant time too (defense in depth)."""
    svc = _service(session)
    user = await _user(session, "self@example.com", AgeBand.UNDER_16)
    link = GuardianLink(
        id=new_uuid(),
        child_user_id=user.id,
        guardian_user_id=user.id,  # self
        relationship="self",
        verification_method=VerificationMethod.EMAIL,
        assurance_level=AssuranceLevel.LOW,
        verified_at=datetime(2026, 1, 1),
    )
    session.add(link)
    await session.flush()
    with pytest.raises(SelfConsentError):
        await svc.grant_consent(guardian_user_id=user.id, guardian_link_id=link.id)
