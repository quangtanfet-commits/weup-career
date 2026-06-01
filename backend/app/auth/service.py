"""AuthService — pure business logic (no FastAPI imports), hexagonal (ADR-009).

Covers register (FR-01 + consent gate FR-02), login (FR-05), atomic refresh
rotation (CP-7), logout revocation, and the `me` lookup.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.auth.age import derive_age_band
from app.auth.models import RefreshToken, User
from app.auth.repository import IRefreshTokenRepo, IRevokedTokenRepo, IUserRepo
from app.auth.schemas import LoginRequest, RegisterRequest
from app.core.audit import IAuditRepo
from app.core.config import Settings
from app.core.enums import AccountStatus, AgeBand, Role, UserType
from app.core.exceptions import (
    InvalidCredentialsError,
    TokenError,
)
from app.core.models import new_uuid, utcnow
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.core.trace import emit as trace_emit
from app.core.trace import token_label


@dataclass(frozen=True)
class IssuedTokens:
    """Result of issuing a session: access JWT + raw refresh token (cookie)."""

    access_token: str
    refresh_token: str
    expires_in: int
    user: User


def _roles_for(user: User) -> list[str]:
    base = Role.WORKING if user.user_type == UserType.WORKING else Role.STUDENT
    roles = [base.value]
    # Global content-editor capability (FR-90). The claim is a fast hint; the
    # content routes still re-derive authority from the DB flag per request.
    if user.is_content_editor:
        roles.append(Role.CONTENT_EDITOR.value)
    return roles


class AuthService:
    def __init__(
        self,
        *,
        settings: Settings,
        users: IUserRepo,
        tokens: IRefreshTokenRepo,
        revoked: IRevokedTokenRepo,
        audit: IAuditRepo,
    ) -> None:
        self._settings = settings
        self._users = users
        self._tokens = tokens
        self._revoked = revoked
        self._audit = audit

    # -- registration -----------------------------------------------------

    async def register(self, payload: RegisterRequest) -> User:
        age_band = derive_age_band(
            payload.date_of_birth,
            threshold=self._settings.consent_age_threshold,
        )
        # FR-02: under-16 starts pending guardian consent.
        account_status = (
            AccountStatus.PENDING_GUARDIAN_CONSENT
            if age_band == AgeBand.UNDER_16
            else AccountStatus.ACTIVE
        )

        existing = await self._users.get_by_email(payload.email)
        if existing is not None:
            # PT-04: do not leak that the email is taken. Return an
            # indistinguishable synthesized 201 derived purely from the
            # submitted payload — fresh random id (never the existing user's),
            # request-derived fields, explicit created_at (no flush to fill it)
            # — as a pure no-op: no DB write, no mutation of the existing
            # account. Burn the same bcrypt cost as the real path to equalise
            # timing, and audit defender-side only (attacker never sees it).
            # See docs/security/email-enumeration.md.
            verify_password(payload.password, _DUMMY_HASH)
            await self._audit.record(
                action="auth.register.duplicate_suppressed",
                actor_id=existing.id,
                target_type="User",
                target_id=existing.id,
            )
            return User(
                id=new_uuid(),
                email=payload.email,
                hashed_password="",
                date_of_birth=payload.date_of_birth,
                age_band=age_band,
                user_type=payload.user_type,
                school_level=payload.school_level,
                account_status=account_status,
                created_at=utcnow(),
            )

        user = User(
            id=new_uuid(),
            email=payload.email,
            hashed_password=hash_password(payload.password, rounds=self._settings.bcrypt_rounds),
            date_of_birth=payload.date_of_birth,
            age_band=age_band,
            user_type=payload.user_type,
            school_level=payload.school_level,
            account_status=account_status,
        )
        await self._users.add(user)
        await self._audit.record(
            action="auth.register.succeeded",
            actor_id=user.id,
            target_type="User",
            target_id=user.id,
        )
        return user

    # -- login ------------------------------------------------------------

    async def login(
        self,
        payload: LoginRequest,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens:
        user = await self._users.get_by_email(payload.email)
        # Constant-ish: always run a verify to avoid user-enumeration timing.
        if user is None:
            verify_password(payload.password, _DUMMY_HASH)
            raise InvalidCredentialsError()
        if not verify_password(payload.password, user.hashed_password):
            await self._audit.record(
                action="auth.login.failed", actor_id=user.id, target_type="User"
            )
            raise InvalidCredentialsError()

        # A soft-deleted account cannot authenticate (FR-91/92). Surfaced as
        # InvalidCredentials (401) so the deletion is not disclosed; the account
        # stays unauthenticable until purged (or recovered, future).
        if user.is_deleted or user.account_status == AccountStatus.DELETED:
            await self._audit.record(
                action="auth.login.rejected_deleted", actor_id=user.id, target_type="User"
            )
            raise InvalidCredentialsError()

        # H-02: bump the session epoch on every successful login so any
        # previously leaked *bare* access token (sv now stale) is rejected.
        # Legitimate devices are unaffected — their refresh cookie re-issues an
        # access token at the new epoch on the next refresh.
        user.session_version += 1
        await self._users.update(user)
        tokens = await self._issue_session(user, user_agent=user_agent, ip_address=ip_address)
        await self._audit.record(
            action="auth.login.succeeded", actor_id=user.id, target_type="User"
        )
        # Gate B trace: spec action Issue (new active token for the user).
        trace_emit(
            "Issue",
            user=user.id,
            state={"token": token_label(hash_refresh_token(tokens.refresh_token))},
        )
        return tokens

    # -- refresh rotation (CP-7) -----------------------------------------

    async def refresh(
        self,
        raw_refresh_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> IssuedTokens:
        token_hash = hash_refresh_token(raw_refresh_token)
        stored = await self._tokens.get_by_hash(token_hash)
        now = datetime.now(UTC)

        if stored is None:
            raise TokenError()
        if stored.revoked_at is not None:
            # Re-use of a rotated/[CRED_19DCD7CE] token → revoke the whole family (CP-7,
            # auth-design §"Re-use detection"). Record audit first so it lands in
            # the same committed unit of work as the revocation (which the repo
            # commits immediately, surviving the 401 that follows).
            await self._audit.record(
                action="auth.token.reuse_detected",
                actor_id=stored.user_id,
                target_type="RefreshToken",
            )
            await self._tokens.revoke_all_for_user(stored.user_id, when=now)
            raise TokenError()
        if _as_utc(stored.expires_at) <= now:
            raise TokenError()

        user = await self._users.get_by_id(stored.user_id)
        if user is None:
            raise TokenError()
        # A soft-deleted account cannot refresh into a new session (FR-91/92).
        if user.is_deleted or user.account_status == AccountStatus.DELETED:
            await self._tokens.revoke(stored, when=now)
            raise TokenError()

        # Atomic rotation: revoke old, mint new — same unit of work (CP-7).
        await self._tokens.revoke(stored, when=now)
        tokens = await self._issue_session(
            user, user_agent=user_agent, ip_address=ip_address, now=now
        )
        await self._audit.record(
            action="auth.token.refreshed", actor_id=user.id, target_type="RefreshToken"
        )
        # Gate B trace: spec action Rotate (old revoked + new active, atomic — CP-7).
        trace_emit(
            "Rotate",
            user=user.id,
            state={
                "old": token_label(stored.token_hash),
                "new": token_label(hash_refresh_token(tokens.refresh_token)),
            },
        )
        return tokens

    # -- logout -----------------------------------------------------------

    async def logout(
        self,
        raw_refresh_token: str | None,
        *,
        access_jti: str | None = None,
        access_exp: int | None = None,
        user_id: str | None = None,
    ) -> None:
        now = datetime.now(UTC)
        # H-01: denylist the access-token jti for its remaining TTL so a stolen
        # or post-logout token cannot be replayed (ADR-008 access JWTs are
        # stateless). This runs even with no refresh cookie — an access-only
        # logout must still revoke the bearer token.
        if access_jti and access_exp and user_id:
            await self._revoked.add(
                jti=access_jti,
                user_id=user_id,
                expires_at=datetime.fromtimestamp(access_exp, UTC),
            )
            await self._audit.record(
                action="auth.access_revoked", actor_id=user_id, target_type="User"
            )
        if not raw_refresh_token:
            return
        stored = await self._tokens.get_by_hash(hash_refresh_token(raw_refresh_token))
        if stored is not None and stored.revoked_at is None:
            await self._tokens.revoke(stored, when=now)
            await self._audit.record(
                action="auth.logout", actor_id=stored.user_id, target_type="RefreshToken"
            )
            # Gate B trace: spec action Logout (active token → revoked).
            trace_emit(
                "Logout",
                user=stored.user_id,
                state={"token": token_label(stored.token_hash)},
            )

    # -- helpers ----------------------------------------------------------

    async def get_user(self, user_id: str) -> User | None:
        return await self._users.get_by_id(user_id)

    async def _issue_session(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
        now: datetime | None = None,
    ) -> IssuedTokens:
        issued = now or datetime.now(UTC)
        access = create_access_token(
            settings=self._settings,
            subject=user.id,
            email=user.email,
            user_type=user.user_type.value,
            age_band=user.age_band.value,
            account_status=user.account_status.value,
            roles=_roles_for(user),
            session_version=user.session_version,
            now=issued,
        )
        raw_refresh = generate_refresh_token()
        refresh_row = RefreshToken(
            id=new_uuid(),
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=issued + timedelta(days=self._settings.refresh_token_expire_days),
            created_at=utcnow(),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        await self._tokens.add(refresh_row)
        return IssuedTokens(
            access_token=access,
            refresh_token=raw_refresh,
            expires_in=self._settings.access_token_expire_minutes * 60,
            user=user,
        )


def _as_utc(value: datetime) -> datetime:
    """Normalise a possibly-naive DB timestamp to aware UTC for comparison."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


# Pre-computed bcrypt hash of a random string, used to equalise login timing for
# unknown emails (avoids user enumeration via response time).
_DUMMY_HASH = hash_password("dummy-password-for-timing-equalisation-A1", rounds=12)
