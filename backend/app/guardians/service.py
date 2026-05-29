"""GuardianService — invite / [CRED_2C24711E] / [CRED_92EC5BFE] (CP-1, CP-2, ADR-010).

Self-consent is forbidden (a child cannot be their own guardian). Granting an
active consent flips the child account to ACTIVE; revoking flips it back to
PENDING_GUARDIAN_CONSENT, stopping new career-data processing (CP-2).

Note on slice scope: the real invite uses an independent verification channel
(email/VNeID, guardian-verification.md). Here the invited guardian must already
be a registered user; the link is created `verified` via the email method
(LOW assurance) so the consent flow is end-to-end testable. Strong VNeID
verification + assurance gating is a later slice.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.auth.repository import IUserRepo
from app.core.audit import IAuditRepo
from app.core.enums import AccountStatus, AssuranceLevel, VerificationMethod
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    SelfConsentError,
)
from app.core.models import new_uuid, utcnow
from app.core.trace import emit as trace_emit
from app.guardians.models import GuardianConsent, GuardianLink
from app.guardians.repository import IGuardianRepo
from app.guardians.schemas import InviteRequest


class GuardianService:
    def __init__(
        self,
        *,
        users: IUserRepo,
        guardians: IGuardianRepo,
        audit: IAuditRepo,
    ) -> None:
        self._users = users
        self._guardians = guardians
        self._audit = audit

    async def invite(self, *, child_user_id: str, payload: InviteRequest) -> GuardianLink:
        child = await self._users.get_by_id(child_user_id)
        if child is None:
            raise NotFoundError("Không tìm thấy tài khoản trẻ")

        guardian = await self._users.get_by_email(payload.guardian_email)
        if guardian is None:
            raise NotFoundError("Người giám hộ chưa có tài khoản")

        # CP-1 / [CRED_A3FA0BC0]: forbid self-consent.
        if guardian.id == child_user_id:
            raise SelfConsentError()

        existing = await self._guardians.get_link_for_child_guardian(
            child_user_id=child_user_id, guardian_user_id=guardian.id
        )
        if existing is not None:
            raise ConflictError("Liên kết giám hộ đã tồn tại")

        link = GuardianLink(
            id=new_uuid(),
            child_user_id=child_user_id,
            guardian_user_id=guardian.id,
            relationship=payload.relationship,
            verification_method=VerificationMethod.EMAIL,
            assurance_level=AssuranceLevel.LOW,
            verified_at=utcnow(),
        )
        await self._guardians.add_link(link)
        await self._audit.record(
            action="guardian.invited",
            actor_id=child_user_id,
            target_type="GuardianLink",
            target_id=link.id,
        )
        return link

    async def grant_consent(
        self, *, guardian_user_id: str, guardian_link_id: str
    ) -> GuardianConsent:
        link = await self._guardians.get_link(guardian_link_id)
        # 404 when the link is absent or not owned by this guardian (no leak).
        if link is None or link.guardian_user_id != guardian_user_id:
            raise NotFoundError("Không tìm thấy liên kết giám hộ")
        if link.verified_at is None:
            raise PermissionDeniedError("Liên kết giám hộ chưa được xác thực")
        if link.guardian_user_id == link.child_user_id:
            raise SelfConsentError()

        if await self._guardians.has_active_consent(link.child_user_id):
            raise ConflictError("Đã có đồng ý đang hoạt động")

        consent = GuardianConsent(
            id=new_uuid(),
            child_user_id=link.child_user_id,
            guardian_link_id=link.id,
        )
        await self._guardians.add_consent(consent)

        child = await self._users.get_by_id(link.child_user_id)
        if child is not None:
            child.account_status = AccountStatus.ACTIVE
            await self._users.update(child)

        await self._audit.record(
            action="guardian.consent.granted",
            actor_id=guardian_user_id,
            target_type="GuardianConsent",
            target_id=consent.id,
        )
        # Gate B conformance trace: spec action GrantConsent (consent → active).
        trace_emit("GrantConsent", user=link.child_user_id, state={"consent": "active"})
        return consent

    async def revoke_consent(self, *, guardian_user_id: str, child_user_id: str) -> None:
        link = await self._guardians.get_link_for_child_guardian(
            child_user_id=child_user_id, guardian_user_id=guardian_user_id
        )
        if link is None:
            raise NotFoundError("Không tìm thấy liên kết giám hộ")

        consent = await self._guardians.get_active_consent(child_user_id)
        if consent is None:
            raise NotFoundError("Không có đồng ý đang hoạt động để thu hồi")

        await self._guardians.revoke_consent(consent, when=datetime.now(UTC))

        # CP-2: child returns to pending — new processing is blocked immediately.
        child = await self._users.get_by_id(child_user_id)
        if child is not None:
            child.account_status = AccountStatus.PENDING_GUARDIAN_CONSENT
            await self._users.update(child)

        await self._audit.record(
            action="guardian.consent.revoked",
            actor_id=guardian_user_id,
            target_type="GuardianConsent",
            target_id=consent.id,
        )
        # Gate B conformance trace: spec action RevokeConsent (consent → revoked).
        trace_emit("RevokeConsent", user=child_user_id, state={"consent": "revoked"})
