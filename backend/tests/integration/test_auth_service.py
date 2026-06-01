"""Service-level tests for AuthService edge paths (CP-7 internals) + repos.

These drive branches that are awkward to reach through HTTP: unknown/[CRED_55BB0BBF]
tokens, a token whose user vanished, naive-datetime normalisation, logout
no-ops, and the audit count helpers (CP-3 monitoring).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.auth.models import RefreshToken, User
from app.auth.repository import (
    SqlRefreshTokenRepo,
    SqlRevokedTokenRepo,
    SqlUserRepo,
)
from app.auth.schemas import LoginRequest, RegisterRequest
from app.auth.service import AuthService, _as_utc
from app.core.audit import SqlAuditRepo
from app.core.config import Settings
from app.core.enums import AccountStatus, AgeBand, UserType
from app.core.exceptions import TokenError
from app.core.models import new_uuid, utcnow
from app.core.security import decode_access_token, hash_refresh_token
from sqlalchemy.ext.asyncio import AsyncSession


def _service(session: AsyncSession, settings: Settings) -> AuthService:
    return AuthService(
        settings=settings,
        users=SqlUserRepo(session),
        tokens=SqlRefreshTokenRepo(session),
        revoked=SqlRevokedTokenRepo(session),
        audit=SqlAuditRepo(session),
    )


async def _make_user(session: AsyncSession) -> User:
    user = User(
        id=new_uuid(),
        email=f"{new_uuid()}@example.com",
        hashed_password="x",
        date_of_birth=datetime(2000, 1, 1).date(),
        age_band=AgeBand.ADULT,
        user_type=UserType.STUDENT,
        account_status=AccountStatus.ACTIVE,
    )
    session.add(user)
    await session.flush()
    return user


async def test_refresh_unknown_token_raises(session: AsyncSession, settings: Settings) -> None:
    svc = _service(session, settings)
    with pytest.raises(TokenError):
        await svc.refresh("never-issued-token")


async def test_refresh_expired_token_raises(session: AsyncSession, settings: Settings) -> None:
    svc = _service(session, settings)
    user = await _make_user(session)
    raw = "expired-raw-token"
    session.add(
        RefreshToken(
            id=new_uuid(),
            user_id=user.id,
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
            created_at=utcnow(),
        )
    )
    await session.flush()
    with pytest.raises(TokenError):
        await svc.refresh(raw)


async def test_refresh_with_missing_user_raises(session: AsyncSession, settings: Settings) -> None:
    svc = _service(session, settings)
    raw = "orphan-token"
    session.add(
        RefreshToken(
            id=new_uuid(),
            user_id="nonexistent-user-id",
            token_hash=hash_refresh_token(raw),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            created_at=utcnow(),
        )
    )
    await session.flush()
    with pytest.raises(TokenError):
        await svc.refresh(raw)


async def test_refresh_rejected_for_soft_deleted_user(
    session: AsyncSession, settings: Settings
) -> None:
    """A soft-deleted account cannot refresh into a new session (FR-91/92).

    Drives the deleted-user branch directly with a still-live (non-revoked)
    token: the refresh is rejected and the presented token is revoked.
    """
    svc = _service(session, settings)
    user = await _make_user(session)
    user.account_status = AccountStatus.DELETED
    user.is_deleted = True
    user.deleted_at = utcnow()
    raw = "live-token-for-deleted-user"
    token = RefreshToken(
        id=new_uuid(),
        user_id=user.id,
        token_hash=hash_refresh_token(raw),
        expires_at=datetime.now(UTC) + timedelta(days=1),
        created_at=utcnow(),
    )
    session.add(token)
    await session.flush()

    with pytest.raises(TokenError):
        await svc.refresh(raw)
    assert token.revoked_at is not None


async def test_login_rejected_for_soft_deleted_user(
    session: AsyncSession, settings: Settings
) -> None:
    """A soft-deleted account cannot log in even with correct credentials."""
    from app.core.exceptions import InvalidCredentialsError
    from app.core.security import hash_password

    svc = _service(session, settings)
    user = await _make_user(session)
    user.hashed_password = hash_password("Password123", rounds=settings.bcrypt_rounds)
    user.account_status = AccountStatus.DELETED
    user.is_deleted = True
    await session.flush()

    with pytest.raises(InvalidCredentialsError):
        await svc.login(LoginRequest(email=user.email, password="Password123"))


async def test_logout_noop_on_empty_token(session: AsyncSession, settings: Settings) -> None:
    svc = _service(session, settings)
    await svc.logout(None)
    await svc.logout("")  # both are no-ops, no exception


async def test_logout_noop_on_unknown_token(session: AsyncSession, settings: Settings) -> None:
    svc = _service(session, settings)
    await svc.logout("not-a-real-token")


async def test_full_register_login_refresh_cycle(session: AsyncSession, settings: Settings) -> None:
    svc = _service(session, settings)
    user = await svc.register(
        RegisterRequest(
            email="cycle@example.com",
            password="Password123",
            date_of_birth=datetime(2000, 1, 1).date(),
            user_type=UserType.STUDENT,
        )
    )
    assert user.account_status == AccountStatus.ACTIVE
    issued = await svc.login(
        LoginRequest(email="cycle@example.com", password="Password123"),
        user_agent="pytest",
        ip_address="127.0.0.1",
    )
    rotated = await svc.refresh(issued.refresh_token)
    assert rotated.access_token
    # Old token now revoked → reuse triggers family revocation + raises.
    with pytest.raises(TokenError):
        await svc.refresh(issued.refresh_token)


def test_as_utc_normalises_naive() -> None:
    naive = datetime(2026, 1, 1, 12, 0, 0)
    assert _as_utc(naive).tzinfo is UTC
    aware = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    assert _as_utc(aware) == aware


async def test_audit_count_helpers(session: AsyncSession, settings: Settings) -> None:
    audit = SqlAuditRepo(session)
    assert await audit.count() == 0
    await audit.record(action="x.event", actor_id="u1")
    await audit.record(action="x.read", actor_id="u1", is_sensitive_access=True)
    assert await audit.count() == 2
    assert await audit.count_sensitive() == 1


async def test_revoke_all_for_user(session: AsyncSession, settings: Settings) -> None:
    repo = SqlRefreshTokenRepo(session)
    user = await _make_user(session)
    for i in range(3):
        await repo.add(
            RefreshToken(
                id=new_uuid(),
                user_id=user.id,
                token_hash=hash_refresh_token(f"t{i}"),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                created_at=utcnow(),
            )
        )
    revoked = await repo.revoke_all_for_user(user.id, when=datetime.now(UTC))
    assert revoked == 3
    # Idempotent: nothing left active to revoke.
    assert await repo.revoke_all_for_user(user.id, when=datetime.now(UTC)) == 0


# -- H-01 access-token denylist --------------------------------------------


async def test_revoked_repo_add_then_is_revoked(session: AsyncSession, settings: Settings) -> None:
    repo = SqlRevokedTokenRepo(session)
    user = await _make_user(session)
    now = datetime.now(UTC)
    await repo.add(jti="jti-live", user_id=user.id, expires_at=now + timedelta(minutes=15))
    assert await repo.is_revoked("jti-live", now=now) is True
    # An unknown jti is never revoked.
    assert await repo.is_revoked("jti-absent", now=now) is False


async def test_revoked_repo_expired_entry_treated_as_absent(
    session: AsyncSession, settings: Settings
) -> None:
    """is_revoked filters on expires_at > now, so correctness never depends on
    pruning having run: a row past its expiry reads as absent."""
    repo = SqlRevokedTokenRepo(session)
    user = await _make_user(session)
    now = datetime.now(UTC)
    await repo.add(jti="jti-stale", user_id=user.id, expires_at=now - timedelta(seconds=1))
    assert await repo.is_revoked("jti-stale", now=now) is False


async def test_revoked_repo_add_is_idempotent(session: AsyncSession, settings: Settings) -> None:
    """Double logout reuses the same jti (unique column) — re-adding is a no-op,
    not an IntegrityError."""
    repo = SqlRevokedTokenRepo(session)
    user = await _make_user(session)
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=15)
    await repo.add(jti="jti-dup", user_id=user.id, expires_at=exp)
    await repo.add(jti="jti-dup", user_id=user.id, expires_at=exp)  # no error
    assert await repo.is_revoked("jti-dup", now=now) is True


async def test_revoked_repo_add_prunes_expired_rows(
    session: AsyncSession, settings: Settings
) -> None:
    """Each add() opportunistically drops inert rows so the table stays bounded
    by the access-token TTL rather than growing per logout forever."""
    from app.auth.models import RevokedAccessToken
    from sqlalchemy import func, select

    repo = SqlRevokedTokenRepo(session)
    user = await _make_user(session)
    now = datetime.now(UTC)
    await repo.add(jti="jti-old", user_id=user.id, expires_at=now - timedelta(seconds=1))
    # Insert a fresh entry — its add() prunes the expired "jti-old".
    await repo.add(jti="jti-new", user_id=user.id, expires_at=now + timedelta(minutes=15))
    count = await session.scalar(select(func.count()).select_from(RevokedAccessToken))
    assert count == 1


async def test_logout_denylists_access_jti(session: AsyncSession, settings: Settings) -> None:
    """Access-only logout (no refresh cookie) still revokes the bearer jti."""
    svc = _service(session, settings)
    user = await _make_user(session)
    now = datetime.now(UTC)
    exp = int((now + timedelta(minutes=15)).timestamp())
    await svc.logout(None, access_jti="jti-logout", access_exp=exp, user_id=user.id)
    repo = SqlRevokedTokenRepo(session)
    assert await repo.is_revoked("jti-logout", now=now) is True


async def test_logout_idempotent_on_same_jti(session: AsyncSession, settings: Settings) -> None:
    """Logging out twice with the same access token leaves exactly one row."""
    from app.auth.models import RevokedAccessToken
    from sqlalchemy import func, select

    svc = _service(session, settings)
    user = await _make_user(session)
    exp = int((datetime.now(UTC) + timedelta(minutes=15)).timestamp())
    await svc.logout(None, access_jti="jti-twice", access_exp=exp, user_id=user.id)
    await svc.logout(None, access_jti="jti-twice", access_exp=exp, user_id=user.id)
    count = await session.scalar(
        select(func.count())
        .select_from(RevokedAccessToken)
        .where(RevokedAccessToken.jti == "jti-twice")
    )
    assert count == 1


# -- H-02 session-version epoch ---------------------------------------------


async def test_user_repo_current_session_version(session: AsyncSession, settings: Settings) -> None:
    """Light single-column read: 1 for a fresh user, follows bumps, None when absent."""
    repo = SqlUserRepo(session)
    user = await _make_user(session)
    assert await repo.current_session_version(user.id) == 1
    user.session_version += 1
    await session.flush()
    assert await repo.current_session_version(user.id) == 2
    assert await repo.current_session_version("nonexistent-user-id") is None


async def test_login_bumps_session_version_and_stamps_token(
    session: AsyncSession, settings: Settings
) -> None:
    """Every successful login increments the epoch and stamps it on the ``sv``
    claim, so a token minted by an earlier login is now below the live value."""
    svc = _service(session, settings)
    await svc.register(
        RegisterRequest(
            email="sv@example.com",
            password="Password123",
            date_of_birth=datetime(2000, 1, 1).date(),
            user_type=UserType.STUDENT,
        )
    )
    first = await svc.login(LoginRequest(email="sv@example.com", password="Password123"))
    second = await svc.login(LoginRequest(email="sv@example.com", password="Password123"))

    sv_first = decode_access_token(first.access_token, settings=settings)["sv"]
    sv_second = decode_access_token(second.access_token, settings=settings)["sv"]
    assert sv_second == sv_first + 1
    # The live epoch matches the most recent login's token.
    repo = SqlUserRepo(session)
    assert await repo.current_session_version(second.user.id) == sv_second


async def test_stale_session_guard_skips_when_sv_claim_absent(
    session: AsyncSession, settings: Settings
) -> None:
    """Legacy tokens minted before H-02 carry no ``sv`` claim — the guard must
    fall through (no raise) so a deploy does not mass-401 live sessions."""
    from app.api.deps import _reject_if_stale_session

    repo = SqlUserRepo(session)
    # No ``sv`` key at all → skip, even though the subject does not exist.
    await _reject_if_stale_session({"sub": "whoever"}, repo)


async def test_stale_session_guard_skips_when_user_absent(
    session: AsyncSession, settings: Settings
) -> None:
    """A token whose subject no longer exists is left to other guards (the user
    lookup will 401 downstream); the epoch check itself does not raise."""
    from app.api.deps import _reject_if_stale_session

    repo = SqlUserRepo(session)
    await _reject_if_stale_session({"sub": "nonexistent-user-id", "sv": 5}, repo)


async def test_stale_session_guard_raises_on_below_epoch_token(
    session: AsyncSession, settings: Settings
) -> None:
    """A token stamped with an ``sv`` below the user's live epoch is rejected."""
    from app.api.deps import _reject_if_stale_session
    from app.core.exceptions import AuthenticationError

    repo = SqlUserRepo(session)
    user = await _make_user(session)
    user.session_version = 3
    await session.flush()
    # A token minted at epoch 2 is now below the live epoch 3 → reject.
    with pytest.raises(AuthenticationError):
        await _reject_if_stale_session({"sub": user.id, "sv": 2}, repo)
    # A token at the live epoch is accepted.
    await _reject_if_stale_session({"sub": user.id, "sv": 3}, repo)
