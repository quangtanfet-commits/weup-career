"""AccountService — data-subject rights, no FastAPI imports (hexagonal, ADR-009).

Implements FR-91 (view/edit profile, change password, soft-delete with recovery
window) and FR-92 (data export incl. decrypted sensitive results). A verified
guardian may exercise export/deletion on behalf of a linked under-16 child
(FR-14/92, CP-4): the actor is resolved through ``can_access`` and every op is
audited with ``actor_id`` = the acting user (guardian when acting for a child).

Key invariants preserved:
- **CP-3:** the export reads decrypted sensitive results, so it writes one
  sensitive-access (``is_sensitive_access=True``) audit row in the SAME session.
- **CP-4:** export/delete of another user's data is only possible via a verified
  guardian link; an unauthorised relation surfaces as NotFound (404).
- **Password safety:** a wrong current password raises before any hash is
  written, so the stored password is never changed on a failed attempt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.account.repository import IAccountRepo
from app.account.schemas import (
    DataExport,
    DeletionOut,
    ProfileOut,
    ProfileUpdateRequest,
)
from app.auth.models import User
from app.auth.repository import IRefreshTokenRepo, IUserRepo
from app.core.audit import IAuditRepo
from app.core.authz import can_access
from app.core.config import Settings
from app.core.crypto import FieldCrypto, FieldCryptoError
from app.core.enums import AccountStatus
from app.core.exceptions import InvalidCredentialsError, NotFoundError
from app.core.models import utcnow
from app.core.security import hash_password, verify_password
from app.guardians.repository import IGuardianRepo


@dataclass(frozen=True)
class DeletionResult:
    """Soft-deletion outcome: the affected user + the concrete deletion/purge
    timestamps (both non-optional, captured at the moment of deletion)."""

    user: User
    deleted_at: datetime
    purge_due_at: datetime


class AccountService:
    def __init__(
        self,
        *,
        settings: Settings,
        users: IUserRepo,
        tokens: IRefreshTokenRepo,
        accounts: IAccountRepo,
        guardians: IGuardianRepo,
        audit: IAuditRepo,
        crypto: FieldCrypto,
    ) -> None:
        self._settings = settings
        self._users = users
        self._tokens = tokens
        self._accounts = accounts
        self._guardians = guardians
        self._audit = audit
        self._crypto = crypto

    # -- subject resolution (CP-4) ----------------------------------------

    async def _resolve_subject(self, *, actor_id: str, subject_id: str) -> User:
        """Return the target user iff ``actor_id`` may act on ``subject_id``.

        Self always allowed; otherwise only a verified guardian of the subject
        (CP-4). Unauthorised → 404 (no existence disclosure, auth-design §"Defense
        in depth"). A non-existent subject is also 404.
        """
        allowed = await can_access(
            actor_id=actor_id, owner_id=subject_id, guardian_repo=self._guardians
        )
        if not allowed:
            raise NotFoundError("Không tìm thấy người dùng")
        subject = await self._users.get_by_id(subject_id)
        if subject is None:
            raise NotFoundError("Không tìm thấy người dùng")
        return subject

    # -- profile view/edit (FR-91) ----------------------------------------

    async def get_profile(self, user_id: str) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("Không tìm thấy người dùng")
        return user

    async def update_profile(self, *, user_id: str, payload: ProfileUpdateRequest) -> User:
        """Update only the SAFE fields supplied (FR-91). Protected fields are not
        part of the schema, so they can never be reached through this route."""
        user = await self.get_profile(user_id)
        if payload.school_level is not None:
            user.school_level = payload.school_level
        if payload.user_type is not None:
            user.user_type = payload.user_type
        await self._users.update(user)
        await self._audit.record(
            action="user.profile_updated",
            actor_id=user_id,
            target_type="User",
            target_id=user_id,
        )
        return user

    # -- change password (FR-91) ------------------------------------------

    async def change_password(
        self, *, user_id: str, current_password: str, new_password: str
    ) -> None:
        """Verify the current password, then re-hash + store the new one.

        A wrong current password raises ``InvalidCredentialsError`` (401) BEFORE
        any write, so the stored hash is left unchanged on a failed attempt.
        On success all refresh tokens are revoked (session invalidation): the
        password just changed, so existing sessions should not survive (CP-7
        spirit). Audited as ``user.password_changed``.
        """
        user = await self.get_profile(user_id)
        if not verify_password(current_password, user.hashed_password):
            await self._audit.record(
                action="user.password_change_failed",
                actor_id=user_id,
                target_type="User",
                target_id=user_id,
            )
            raise InvalidCredentialsError("Mật khẩu hiện tại không đúng")

        user.hashed_password = hash_password(new_password, rounds=self._settings.bcrypt_rounds)
        await self._users.update(user)
        # Revoke all active refresh tokens: a password change invalidates
        # existing sessions (reuse of the existing family-revoke primitive).
        await self._tokens.revoke_all_for_user(user_id, when=utcnow())
        await self._audit.record(
            action="user.password_changed",
            actor_id=user_id,
            target_type="User",
            target_id=user_id,
        )

    # -- data export (FR-92, CP-3) ----------------------------------------

    async def export_data(self, *, actor_id: str, subject_id: str) -> DataExport:
        """Export all of the subject's personal data (FR-92).

        Reads DECRYPTED assessment results, so exactly one sensitive-access
        audit row is written in the same session (CP-3) BEFORE the bundle is
        returned. The export action itself is also audited.
        """
        subject = await self._resolve_subject(actor_id=actor_id, subject_id=subject_id)

        results = await self._accounts.list_results(subject.id)
        progress = await self._accounts.list_progress(subject.id)
        phases = await self._accounts.list_domain_phases(subject.id)
        recos = await self._accounts.list_recommendations(subject.id)

        # CP-3: any export that includes decrypted sensitive results writes a
        # sensitive-access audit row, in the same transaction, before returning.
        if results:
            await self._audit.record(
                action="assessment.result.exported",
                actor_id=actor_id,
                target_type="AssessmentResult",
                target_id=subject.id,
                is_sensitive_access=True,
            )

        result_dicts: list[dict[str, object]] = []
        for r in results:
            result_dicts.append(
                {
                    "id": r.id,
                    "instrument_id": r.instrument_id,
                    "version": r.version,
                    "is_sensitive": r.is_sensitive,
                    "created_at": r.created_at.isoformat(),
                    # Decrypted payload (the data subject's own data).
                    "payload": _decrypt_payload(self._crypto, r.result_payload),
                }
            )

        export = DataExport(
            exported_at=utcnow(),
            subject_id=subject.id,
            profile=ProfileOut.model_validate(subject),
            assessment_results=result_dicts,
            competency_progress=[
                {
                    "competency_id": p.competency_id,
                    "depth_achieved": p.depth_achieved.value,
                    "evidence_ref": p.evidence_ref,
                    "achieved_at": p.achieved_at.isoformat(),
                }
                for p in progress
            ],
            domain_phases=[
                {
                    "area": ph.area.value,
                    "dev_phase": ph.dev_phase.value,
                    "set_at": ph.set_at.isoformat(),
                }
                for ph in phases
            ],
            recommendations=[
                {
                    "id": rc.id,
                    "payload": rc.payload,
                    "rationale": rc.rationale,
                    "requires_human_confirmation": rc.requires_human_confirmation,
                    "confirmed_decision": (
                        rc.confirmed_decision.value if rc.confirmed_decision else None
                    ),
                    "created_at": rc.created_at.isoformat(),
                }
                for rc in recos
            ],
        )

        # Always audit the export action itself (data-subject right exercised).
        await self._audit.record(
            action="user.data_exported",
            actor_id=actor_id,
            target_type="User",
            target_id=subject.id,
        )
        return export

    # -- account deletion = soft delete + recovery window (FR-91/92) ------

    async def soft_delete(self, *, actor_id: str, subject_id: str) -> DeletionResult:
        """Soft-delete the subject's account (FR-91/92).

        Sets ``account_status=deleted``, ``is_deleted=True``, ``deleted_at=now``.
        Data is RETAINED during the recovery window; a scheduled purge hard-
        deletes it once the window elapses. All refresh tokens are revoked so the
        account can no longer obtain new access tokens. Audited with the actor id
        (a guardian when acting for a linked child, CP-4).
        """
        subject = await self._resolve_subject(actor_id=actor_id, subject_id=subject_id)
        now = utcnow()
        subject.account_status = AccountStatus.DELETED
        subject.is_deleted = True
        subject.deleted_at = now
        await self._users.update(subject)
        # A deleted account holds no live sessions.
        await self._tokens.revoke_all_for_user(subject.id, when=now)
        await self._audit.record(
            action="user.account_deleted",
            actor_id=actor_id,
            target_type="User",
            target_id=subject.id,
        )
        purge_due = now + timedelta(days=self._settings.account_recovery_window_days)
        return DeletionResult(user=subject, deleted_at=now, purge_due_at=purge_due)

    def deletion_out(self, result: DeletionResult) -> DeletionOut:
        return DeletionOut(
            status=result.user.account_status,
            deleted_at=result.deleted_at,
            purge_due_at=result.purge_due_at,
            recovery_window_days=self._settings.account_recovery_window_days,
        )


def _decrypt_payload(crypto: FieldCrypto, ciphertext: str) -> object:
    """Decrypt + JSON-parse a stored result payload for export.

    Fail-closed: a malformed/forged ciphertext raises rather than leaking
    partial plaintext (FieldCrypto contract).
    """
    plaintext = crypto.decrypt(ciphertext)
    try:
        return json.loads(plaintext)
    except json.JSONDecodeError as exc:  # pragma: no cover - stored payload is always JSON
        raise FieldCryptoError("decrypted payload is not valid JSON") from exc
